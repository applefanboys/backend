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

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_id: int
    is_onboarded: bool

# ✅ [이름 변경됨] PasswordResetRequest -> SimpleResetRequest
# token 필드 없음 (이메일, 새비밀번호만 존재)
class SimpleResetRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, max_length=72)