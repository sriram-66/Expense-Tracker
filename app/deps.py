from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=401, detail="Not authenticated")
    if creds is None:
        raise unauthorized
    user_id = decode_token(creds.credentials)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise unauthorized
    return user
