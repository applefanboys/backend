# 공통 설정 모음 (경로, 토큰 만료일 등)
import os

# App/core 기준 상위 경로 계산
BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
PROJECT_ROOT = os.path.dirname(BASE_DIR)          # <repo root>

# SQLite DB 파일 경로 (루트에 users.db)
DB_PATH = os.path.join(PROJECT_ROOT, "users.db")

# 토큰 만료 기간(일)
TOKEN_TTL_DAYS = 7
