# FastAPI용 Auth 라우터

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from App.service.auth_service import (
    register,
    login_and_issue_token,
    get_user_from_token,
    logout,
    delete_account_by_token,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


# ======== 요청 바디용 스키마 ========

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ======== 엔드포인트들 ========

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def route_register(body: RegisterRequest):
    """회원가입: {username, password} -> 201/400"""
    try:
        register(body.username.strip(), body.password)
    except ValueError as e:
        # Flask의 `return jsonify(...), 400` 대신 HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return {"message": "회원가입 성공"}


@router.post("/login")
async def route_login(body: LoginRequest):
    """로그인: {username, password} -> {token}"""
    try:
        token = login_and_issue_token(body.username.strip(), body.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return {"token": token}


@router.get("/me")
async def route_me(authorization: Optional[str] = Header(default=None)):
    """내 정보: Authorization: Token <token> -> {id, username}"""
    if not authorization or not authorization.startswith("Token "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 없습니다.",
        )

    token = authorization.split(" ", 1)[1]
    user = get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    # service에서 dict를 리턴한다고 가정
    return user


@router.post("/logout")
async def route_logout(authorization: Optional[str] = Header(default=None)):
    """로그아웃: Authorization: Token <token> -> 토큰 삭제"""
    if not authorization or not authorization.startswith("Token "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 없습니다.",
        )

    token = authorization.split(" ", 1)[1]
    if not logout(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 로그아웃됐거나 없는 토큰",
        )

    return {"message": "logout success"}

@router.delete("/me")
async def route_delete_me(authorization: Optional[str] = Header(default=None)):
    """
    회원 탈퇴: Authorization: Token <token> -> 계정 및 세션 삭제
    """
    if not authorization or not authorization.startswith("Token "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 없습니다.",
        )

    token = authorization.split(" ", 1)[1]

    try:
        delete_account_by_token(token)
    except ValueError as e:
        # 토큰이 잘못됐거나, 유저가 없거나, 등등
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 200 또는 204 둘 다 상관 없지만, 지금 스타일 맞춰서 메시지 리턴
    return {"message": "계정이 삭제되었습니다."}
