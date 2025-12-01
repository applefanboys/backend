# App/user/service.py
import uuid
from sqlalchemy.orm import Session
from App.user import models, schemas
from App.core.security import get_password_hash, verify_password

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise ValueError("이미 사용 중인 이메일입니다.")
    
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

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_general_token(db: Session, user_id: int) -> str:
    random_token = str(uuid.uuid4())
    db_token = models.UserToken(token=random_token, user_id=user_id)
    db.add(db_token)
    db.commit()
    return random_token

# ✅ [수정됨] 토큰 검증 없이 바로 비밀번호 변경
def update_password(db: Session, email: str, new_password: str):
    # 1. 유저 확인
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise ValueError("가입되지 않은 이메일입니다.")

    # 2. 비밀번호 암호화 및 업데이트
    user.password_hash = get_password_hash(new_password)
    
    # 3. 저장
    db.commit()
    db.refresh(user)
    return user