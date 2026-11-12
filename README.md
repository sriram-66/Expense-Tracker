# Expense Tracker

A full-stack personal finance app. Users sign up, log in, record expenses, and see monthly spending by category and a 6-month trend.

**Live demo:** https://expense-tracker-csvv.onrender.com

## Features
- Secure signup and login (salted PBKDF2 password hashing, JWT authentication)
- Add, edit, delete, and filter expenses by month and category
- Monthly summary by category and a 6-month spending report with charts
- Each user can only access their own data
- Automated tests (pytest) and CI with GitHub Actions
- Dockerized for deployment

## Tech stack
Python, FastAPI, SQLAlchemy, SQLite, PyJWT, Chart.js, pytest, GitHub Actions, Docker

## Project structure
```
app/
  main.py          app setup
  config.py        settings from environment variables
  database.py      engine and session
  models.py        User and Expense tables
  schemas.py       request/response validation (Pydantic)
  security.py      password hashing and JWT helpers
  deps.py          get_current_user dependency
  routers/
    auth.py        register, login
    expenses.py    CRUD, filters, summary, monthly report
static/index.html  frontend
tests/             API and security tests
```

## Run locally
```bash
pip install -r requirements.txt
export SECRET_KEY=any-long-random-string
uvicorn app.main:app --reload
```
- App: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs

## Run the tests
```bash
pip install -r requirements-dev.txt
pytest -v
```

## Run with Docker
```bash
docker build -t expense-tracker .
docker run -p 8000:8000 -e SECRET_KEY=your-secret expense-tracker
```

## Deploy on Render
1. Push to GitHub.
2. On render.com choose **New > Web Service**, connect the repo, and select the **Docker** runtime.
3. Add the environment variable `SECRET_KEY` (a long random string).
4. Deploy and open the URL.

On free tiers the SQLite file resets on redeploy. For permanent data, attach a persistent disk and set `DATABASE_URL`, or use a hosted PostgreSQL database.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create account, returns token |
| POST | `/api/auth/login` | Log in, returns token |
| GET | `/api/expenses?month=YYYY-MM&category=Food` | List expenses |
| POST | `/api/expenses` | Add an expense |
| PUT | `/api/expenses/{id}` | Update an expense |
| DELETE | `/api/expenses/{id}` | Delete an expense |
| GET | `/api/expenses/summary?month=YYYY-MM` | Total and totals by category |
| GET | `/api/expenses/monthly` | Totals for the last 6 months |

Send the token as `Authorization: Bearer <token>`.

## Design decisions
- **Ownership checks:** every expense query filters by the logged-in user, and other users' records return 404.
- **Validation:** Pydantic rejects negative amounts, short passwords, and bad dates before they reach the database.
- **Testability:** the database is a dependency, so tests swap in an in-memory SQLite database.

## Future improvements
- Budget limits with alerts
- CSV export
- Refresh tokens
- PostgreSQL
