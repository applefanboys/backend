# app/routers/auth_reset.py
from fastapi import Form
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from starlette.responses import HTMLResponse

from App.core.database import get_db
from App.user.models import User
from App.user.password_reset import PasswordResetToken
from App.core.email_utils import send_password_reset_email
from App.core.security import get_password_hash  # 이미 쓰고 있던 함수라고 가정

router = APIRouter(prefix="/api/user", tags=["user"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # 보안상 존재 여부를 노출하지 않는 게 일반적이라
    # user 없더라도 똑같은 메시지 반환
    if not user:
        return {"message": "비밀번호 재설정 링크를 이메일로 전송했습니다."}

    # 토큰 생성 (랜덤 문자열)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(reset_token)
    db.commit()

    # 이메일 전송
    try:
        send_password_reset_email(user.email, token)
    except Exception as e:
        # 로그 찍고, 사용자에게는 일반 메시지
        print(f"[ERROR] Failed to send password reset email: {e}")
        # 상황에 따라 여기서 500 던져도 되고, 그냥 성공 메시지 줘도 됨
        # raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다.")

    return {"message": "비밀번호 재설정 링크를 이메일로 전송했습니다."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_obj = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token)
        .first()
    )

    if not token_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="유효하지 않은 토큰입니다.")

    if token_obj.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="이미 사용된 토큰입니다.")

    if token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="만료된 토큰입니다.")

    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="유효하지 않은 사용자입니다.")

    # 비밀번호 해시 업데이트
    user.password_hash = get_password_hash(payload.new_password)

    # 토큰 사용 처리
    token_obj.used = True

    db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다."}