import uuid
from sqlalchemy.orm import Session
from App.user import models, schemas
from App.core.security import get_password_hash, verify_password

# 회원가입 (기존과 동일)
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

# 로그인 인증 (기존과 동일)
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# [추가됨] 일반 토큰 생성 및 저장
def create_general_token(db: Session, user_id: int) -> str:
    # 1. 랜덤 문자열(UUID) 생성
    random_token = str(uuid.uuid4())
    
    # 2. DB에 저장
    db_token = models.UserToken(
        token=random_token,
        user_id=user_id
    )
    db.add(db_token)
    db.commit()
    
    return random_token