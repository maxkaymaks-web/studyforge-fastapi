from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    bearer_token: Annotated[str | None, Depends(oauth2_scheme)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User | None:
    token = bearer_token or access_token
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        return None
    user = db.scalar(select(User).where(User.id == user_id))
    return user


def get_current_user(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if current_user is None:
        raise credentials_exception
    return current_user
