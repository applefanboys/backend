# App/user/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.user import schemas, service

router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)


@router.post("/signup", response_model=schemas.UserRead)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    회원가입
    """
    try:
        user = service.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return user


@router.post("/login", response_model=schemas.Token)
def login(login_in: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    로그인:
    - 이메일/비번 확인
    - 성공 시 일반 토큰(UUID) 생성 후 반환
    """
    # 1. 유저 인증
    user = service.authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    # 2. 토큰 생성 (service.py에 create_general_token 함수가 있어야 함)
    access_token = service.create_general_token(db, user.id)

    # 3. 안드로이드가 원하는 형태로 반환
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.username,  # DB의 username을 JSON의 user_name 키에 담음
        "user_id": user.id  # 👈 [추가됨] DB의 ID를 전달
    }