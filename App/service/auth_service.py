# 비즈니스 로직 레이어 (검증, 비밀번호 검사, 토큰 발급/만료 체크)
import datetime, secrets
from werkzeug.security import check_password_hash
from App.core.config import TOKEN_TTL_DAYS
from App.repository.user_repository import (
    create_user as repo_create_user,
    find_user_by_username,
    insert_session,
    find_user_by_token,
    delete_user_and_sessions as repo_delete_user_and_sessions,
)

def register(username: str, password: str):
    """회원가입 입력 검증 + 저장."""
    if not username or not password:
        raise ValueError("username과 password는 필수입니다.")
    repo_create_user(username, password)

def login_and_issue_token(username: str, password: str) -> str:
    """로그인 검증 후 랜덤 토큰 발급/저장하고 토큰 문자열 반환."""
    row = find_user_by_username(username)
    if not row:
        raise ValueError("존재하지 않는 사용자입니다.")
    user_id, _, pw_hash = row
    if not check_password_hash(pw_hash, password):
        raise ValueError("비밀번호가 올바르지 않습니다.")
    token = secrets.token_hex(32)  # 64자 hex 토큰
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_TTL_DAYS)).isoformat()
    insert_session(token, user_id, expires_at)
    return token

def get_user_from_token(token: str):
    """토큰으로 사용자 조회 + 만료 여부 확인."""
    row = find_user_by_token(token)
    if not row:
        return None
    user_id, username, expires_at = row
    if datetime.datetime.fromisoformat(expires_at) < datetime.datetime.utcnow():
        return None
    return {"id": user_id, "username": username}

def logout(token: str) -> bool:
    """토큰 삭제(로그아웃)."""
    return repo_delete_session(token)

def delete_account_by_token(token: str) -> None:
    """
    토큰 기준으로 현재 유저 계정을 삭제.
    유효하지 않은 토큰이거나, 이미 삭제된 경우 ValueError 발생.
    """
    user = get_user_from_token(token)

    if not user:
        raise ValueError("유효하지 않은 토큰입니다.")

    # user가 dict인지, 객체인지에 따라 id 꺼내기
    user_id = user["id"] if isinstance(user, dict) else user.id


    deleted = repo_delete_user_and_sessions(user_id)

    if not deleted:
        # 이 케이스는 거의 없겠지만 방어 코드
        raise ValueError("이미 삭제되었거나 존재하지 않는 사용자입니다.")
