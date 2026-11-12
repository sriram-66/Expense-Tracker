import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Expense, User
from ..schemas import ExpenseIn, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def month_range(month: str):
    """'2025-03' -> (2025-03-01, 2025-04-01)"""
    try:
        start = dt.datetime.strptime(month, "%Y-%m").date()
    except ValueError:
        raise HTTPException(400, "month must be in YYYY-MM format")
    end = dt.date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return start, end


def get_owned(db: Session, user: User, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None or expense.user_id != user.id:
        raise HTTPException(404, "Expense not found")
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    month: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Expense).where(Expense.user_id == user.id)
    if month:
        start, end = month_range(month)
        query = query.where(Expense.date >= start, Expense.date < end)
    if category:
        query = query.where(Expense.category == category)
    query = query.order_by(Expense.date.desc(), Expense.id.desc())
    return db.scalars(query).all()


@router.get("/summary")
def summary(
    month: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    month = month or dt.date.today().strftime("%Y-%m")
    start, end = month_range(month)
    conds = [Expense.user_id == user.id, Expense.date >= start, Expense.date < end]

    rows = db.execute(
        select(Expense.category, func.sum(Expense.amount)).where(*conds).group_by(Expense.category)
    ).all()
    by_category = sorted(
        [{"category": c, "total": round(t, 2)} for c, t in rows], key=lambda x: -x["total"]
    )
    count = db.scalar(select(func.count(Expense.id)).where(*conds))
    return {
        "month": month,
        "total": round(sum(x["total"] for x in by_category), 2),
        "count": count,
        "by_category": by_category,
    }


@router.get("/monthly")
def monthly(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Totals for the last 6 months, oldest first."""
    today = dt.date.today()
    keys, y, m = [], today.year, today.month
    for _ in range(6):
        keys.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    keys.reverse()

    start = dt.datetime.strptime(keys[0], "%Y-%m").date()
    rows = db.execute(
        select(Expense.date, Expense.amount).where(Expense.user_id == user.id, Expense.date >= start)
    ).all()
    totals = {k: 0.0 for k in keys}
    for date, amount in rows:
        key = date.strftime("%Y-%m")
        if key in totals:
            totals[key] += amount
    return [{"month": k, "total": round(v, 2)} for k, v in totals.items()]


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(
    data: ExpenseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    expense = Expense(
        user_id=user.id,
        amount=round(data.amount, 2),
        category=data.category.strip(),
        description=data.description.strip(),
        date=data.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    data: ExpenseIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    expense = get_owned(db, user, expense_id)
    expense.amount = round(data.amount, 2)
    expense.category = data.category.strip()
    expense.description = data.description.strip()
    expense.date = data.date
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    expense = get_owned(db, user, expense_id)
    db.delete(expense)
    db.commit()
    return Response(status_code=204)
