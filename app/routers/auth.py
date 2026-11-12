from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import LoginIn, TokenOut, UserCreate
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    username = data.username.lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(409, "Username already taken")
    user = User(username=username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id), username=user.username)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return TokenOut(access_token=create_token(user.id), username=user.username)
