# App/user/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
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


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    login_in: schemas.UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    로그인:
    - 이메일 + 비밀번호 확인
    - 성공 시 user_id를 쿠키에 저장 (간단 세션)
    """
    user = service.authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    # 간단 세션: user_id를 쿠키에 저장
    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True,     # JS에서 못 건드리게
        samesite="lax",    # 기본값(상황 보고 조정 가능)
        # secure=True,     # HTTPS 환경이면 켜는 게 좋음
    )

    return schemas.LoginResponse(user=user)


@router.post("/logout")
def logout(response: Response):
    """
    로그아웃:
    - user_id 쿠키 삭제
    - 서버 쪽에 별도 세션 저장 안 했으므로 이걸로 끝
    """
    response.delete_cookie("user_id")
    return {"message": "로그아웃 되었습니다."}
