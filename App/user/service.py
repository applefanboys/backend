# App/user/service.py
from typing import Optional

from sqlalchemy.orm import Session

from App.core.security import get_password_hash, verify_password
from App.user import models, schemas


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    # 이메일 중복 체크
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise ValueError("이미 사용 중인 이메일입니다.")

    # username 중복 체크
    existing_username = (
        db.query(models.User)
        .filter(models.User.username == user_in.username)
        .first()
    )
    if existing_username:
        raise ValueError("이미 사용 중인 사용자 이름입니다.")

    hashed_pw = get_password_hash(user_in.password)

    user = models.User(
        email=user_in.email,
        username=user_in.username,
        password_hash=hashed_pw,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session, email: str, password: str
) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
