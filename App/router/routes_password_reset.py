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
        expires_at=expires_at
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


@router.get("/reset-password-page", response_class=HTMLResponse)
def reset_password_page(token: str, db: Session = Depends(get_db)):
    """
    브라우저에서 열리는 비밀번호 재설정 폼 페이지
    """
    token_obj = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token)
        .first()
    )

    # 토큰 검증 (없음 / 만료 / 사용됨 등)
    error_msg = None
    if not token_obj:
        error_msg = "유효하지 않은 링크입니다."
    elif token_obj.used:
        error_msg = "이미 사용된 링크입니다."
    elif token_obj.expires_at < datetime.utcnow():
        error_msg = "만료된 링크입니다."

    if error_msg:
        return HTMLResponse(f"""
        <html>
          <body>
            <h3>{error_msg}</h3>
            <p>다시 비밀번호 재설정을 요청해 주세요.</p>
          </body>
        </html>
        """)

    # 정상 토큰이면 비밀번호 입력 폼 보여주기
    return HTMLResponse(f"""
    <html>
      <body>
        <h2>비밀번호 재설정</h2>
        <form method="post" action="/api/user/reset-password-page">
          <input type="hidden" name="token" value="{token}">
          <div>
            <label>새 비밀번호: </label>
            <input type="password" name="new_password" />
          </div>
          <div style="margin-top: 12px;">
            <button type="submit">변경</button>
          </div>
        </form>
      </body>
    </html>
    """)


@router.post("/reset-password-page", response_class=HTMLResponse)
def reset_password_page_submit(
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    브라우저에서 폼으로 들어오는 비밀번호 변경 처리
    (위 /api/user/reset-password와 로직 거의 동일)
    """
    token_obj = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token)
        .first()
    )

    if not token_obj or token_obj.used or token_obj.expires_at < datetime.utcnow():
        return HTMLResponse("""
        <html>
          <body>
            <h3>링크가 유효하지 않습니다.</h3>
            <p>다시 비밀번호 재설정을 요청해 주세요.</p>
          </body>
        </html>
        """)

    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        return HTMLResponse("""
        <html>
          <body>
            <h3>유효하지 않은 사용자입니다.</h3>
          </body>
        </html>
        """)

    user.password_hash = get_password_hash(new_password)
    token_obj.used = True
    db.commit()

    return HTMLResponse("""
    <html>
      <body>
        <h3>비밀번호가 성공적으로 변경되었습니다.</h3>
        <p>이제 앱에서 새 비밀번호로 로그인해 주세요.</p>
      </body>
    </html>
    """)
