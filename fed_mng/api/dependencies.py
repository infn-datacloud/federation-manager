from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from fed_mng.db import get_session
from fed_mng.models import User


def user_exists(user_id: int, session: Session = Depends(get_session)):
    user = session.exec(select(User).filter(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id `{user_id}` does not exist.",
        )
    return user
