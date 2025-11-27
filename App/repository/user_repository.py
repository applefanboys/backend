# 순수 DB 접근 레이어 (SQL만 수행, 비즈니스 로직 없음)
from werkzeug.security import generate_password_hash
from App.db.session import get_db

def find_user_by_username(username: str):
    """username으로 사용자 1명 조회 (없으면 None)."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    conn.close()
    return row  # (id, username, password_hash) or None

def create_user(username: str, password: str):
    """새 사용자 생성. 중복이면 ValueError."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        conn.close()
        raise ValueError("이미 존재하는 username입니다.")
    pw_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
    conn.commit(); conn.close()

def insert_session(token: str, user_id: int, expires_at: str):
    """세션(토큰) 저장."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
                (token, user_id, expires_at))
    conn.commit(); conn.close()

def find_user_by_token(token: str):
    """토큰으로 유저/만료정보 조회."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT users.id, users.username, sessions.expires_at
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = %s""", (token,))
    row = cur.fetchone()
    conn.close()
    return row  # (id, username, expires_at) or None

def delete_session(token: str) -> bool:
    """토큰 삭제(로그아웃). 삭제됐으면 True."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
    deleted = cur.rowcount
    conn.commit(); conn.close()
    return deleted > 0

def delete_user_and_sessions(user_id: int) -> bool:
    """
    주어진 user_id의 세션들을 모두 삭제하고, 마지막에 사용자 계정을 삭제.
    삭제된 사용자가 있으면 True, 없으면 False 리턴.
    """
    conn = get_db()
    cur = conn.cursor()

    # 1) 세션 삭제
    cur.execute(
        """
        DELETE FROM sessions
        WHERE user_id = %s
        """,
        (user_id,)
    )

    # 2) 유저 삭제
    cur.execute(
        """
        DELETE FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    deleted = cur.rowcount  # users 테이블에서 삭제된 행 수
    conn.commit()

    return deleted > 0
