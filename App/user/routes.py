from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from App.core.database import get_db
from App.user import schemas, service

router = APIRouter(prefix="/api/user", tags=["user"])

@router.post("/signup", response_model=schemas.UserRead)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        user = service.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user

@router.post("/login", response_model=schemas.Token)
def login(login_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    access_token = service.create_general_token(db, user.id)
    
    is_onboarded = False
    if user.onboarding and user.onboarding.q2_keywords:
        is_onboarded = True

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.username,
        "user_id": user.id,
        "is_onboarded": is_onboarded
    }

# ✅ [수정됨] schemas.SimpleResetRequest 사용
@router.post("/reset-password")
def reset_password(payload: schemas.SimpleResetRequest, db: Session = Depends(get_db)):
    try:
        # token 인자 없이 바로 업데이트
        service.update_password(db, payload.email, payload.new_password)
        return {"message": "비밀번호가 성공적으로 변경되었습니다."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))