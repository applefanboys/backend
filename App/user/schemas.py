# App/user/schemas.py
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

# ✅ [가장 중요] 앱이 기다리는 이름표("user_name")를 여기에 적어줘야 합니다.
class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str   # 👈 여기가 username이 아니라 user_name 이어야 합니다!
    user_id: int  # 👈 [추가됨] 앱에게 유저 번호를 알려주기 위함