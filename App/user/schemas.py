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
        from_attributes = True  # SQLAlchemy 객체 -> 응답 변환용


class LoginResponse(BaseModel):
    """
    로그인 성공 시 응답 형태
    """
    user: UserRead
    message: str = "로그인 성공"
