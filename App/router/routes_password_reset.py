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


@router.get("/reset-password-open", response_class=HTMLResponse)
async def open_app_password_reset(token: str):
    """
    이메일에서 클릭 시 호출되는 API입니다.
    브라우저를 통해 앱의 Custom Scheme을 실행합니다.
    """
    # 실제 앱으로 보낼 딥링크
    deep_link = f"shorteconomy://reset-password?token={token}"

    # 안드로이드 마켓 링크 (앱이 안 깔려 있을 경우 대비 - 선택 사항)
    # market_link = "market://details?id=com.your.package.name"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>앱으로 이동 중...</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script>
            window.onload = function() {{
                // 1. 앱 딥링크 실행
                window.location.href = "{deep_link}";

                // 2. (선택) 일정 시간 후에도 반응 없으면 안내 메시지 표시
                setTimeout(function() {{
                    document.getElementById("message").innerText = "앱이 자동으로 열리지 않으면 아래 버튼을 눌러주세요.";
                    document.getElementById("btn").style.display = "block";
                }}, 500);
            }};
        </script>
    </head>
    <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
        <h3 id="message">숏뉴스 앱으로 이동합니다...</h3>
        <a id="btn" href="{deep_link}" 
           style="display:none; background-color:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; margin-top:20px;">
           앱 열기
        </a>
    </body>
    </html>
    """
    return html_content