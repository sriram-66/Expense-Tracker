import datetime as dt

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now():
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200), default="")
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    owner: Mapped["User"] = relationship(back_populates="expenses")
