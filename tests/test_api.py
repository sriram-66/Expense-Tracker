import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def register(client, username="alice", password="secret123"):
    res = client.post("/api/auth/register", json={"username": username, "password": password})
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def add_expense(client, headers, amount=100, category="Food", date="2025-01-15", description=""):
    return client.post(
        "/api/expenses",
        headers=headers,
        json={"amount": amount, "category": category, "date": date, "description": description},
    )


# ---------- auth ----------
def test_register_and_login(client):
    register(client)
    res = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_duplicate_username_rejected(client):
    register(client)
    res = client.post("/api/auth/register", json={"username": "Alice", "password": "another123"})
    assert res.status_code == 409


def test_wrong_password_rejected(client):
    register(client)
    res = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert res.status_code == 401


def test_short_password_rejected(client):
    res = client.post("/api/auth/register", json={"username": "bob", "password": "123"})
    assert res.status_code == 422


def test_expenses_require_login(client):
    assert client.get("/api/expenses").status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/api/expenses", headers=bad).status_code == 401


# ---------- expenses ----------
def test_create_and_list_expenses(client):
    h = register(client)
    res = add_expense(client, h, amount=250.5, category="Food", description="Lunch")
    assert res.status_code == 201
    assert res.json()["amount"] == 250.5

    listed = client.get("/api/expenses", headers=h).json()
    assert len(listed) == 1
    assert listed[0]["description"] == "Lunch"


def test_invalid_amount_rejected(client):
    h = register(client)
    assert add_expense(client, h, amount=-5).status_code == 422
    assert add_expense(client, h, amount=0).status_code == 422


def test_users_cannot_see_each_others_expenses(client):
    alice = register(client, "alice")
    bob = register(client, "bobby")
    expense_id = add_expense(client, alice).json()["id"]

    assert client.get("/api/expenses", headers=bob).json() == []
    assert client.delete(f"/api/expenses/{expense_id}", headers=bob).status_code == 404
    assert len(client.get("/api/expenses", headers=alice).json()) == 1


def test_update_and_delete_expense(client):
    h = register(client)
    expense_id = add_expense(client, h, amount=100).json()["id"]

    res = client.put(
        f"/api/expenses/{expense_id}",
        headers=h,
        json={"amount": 175, "category": "Bills", "date": "2025-01-20", "description": "Wifi"},
    )
    assert res.status_code == 200
    assert res.json()["amount"] == 175
    assert res.json()["category"] == "Bills"

    assert client.delete(f"/api/expenses/{expense_id}", headers=h).status_code == 204
    assert client.get("/api/expenses", headers=h).json() == []


def test_filter_by_month_and_category(client):
    h = register(client)
    add_expense(client, h, 100, "Food", "2025-01-10")
    add_expense(client, h, 200, "Rent", "2025-01-12")
    add_expense(client, h, 50, "Food", "2025-02-03")

    jan = client.get("/api/expenses?month=2025-01", headers=h).json()
    assert len(jan) == 2
    food = client.get("/api/expenses?category=Food", headers=h).json()
    assert len(food) == 2
    assert client.get("/api/expenses?month=bad", headers=h).status_code == 400


# ---------- reports ----------
def test_monthly_summary(client):
    h = register(client)
    add_expense(client, h, 100, "Food", "2025-01-10")
    add_expense(client, h, 50.5, "Food", "2025-01-11")
    add_expense(client, h, 200, "Rent", "2025-01-12")
    add_expense(client, h, 999, "Food", "2025-02-01")  # other month

    data = client.get("/api/expenses/summary?month=2025-01", headers=h).json()
    assert data["total"] == 350.5
    assert data["count"] == 3
    assert data["by_category"][0] == {"category": "Rent", "total": 200.0}
    assert data["by_category"][1] == {"category": "Food", "total": 150.5}


def test_last_six_months_report(client):
    h = register(client)
    today = dt.date.today()
    add_expense(client, h, 300, "Food", today.isoformat())

    data = client.get("/api/expenses/monthly", headers=h).json()
    assert len(data) == 6
    assert data[-1]["month"] == today.strftime("%Y-%m")
    assert data[-1]["total"] == 300.0


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
