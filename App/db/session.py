# App/db/session.py
import os
import mysql.connector
from mysql.connector import MySQLConnection
from dotenv import load_dotenv

# .env 읽기
load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "db"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "loguser"),
    "password": os.getenv("MYSQL_PASSWORD", "logpass"),
    "database": os.getenv("MYSQL_DB", "logdb"),
}



def get_db() -> MySQLConnection:
    """MySQL 연결 생성 후 반환"""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn


def init_db():
    """서버 시작 시 MySQL 테이블 생성"""
    conn = get_db()
    cur = conn.cursor()

    # users 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # sessions 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token VARCHAR(255) PRIMARY KEY,
            user_id INT NOT NULL,
            expires_at VARCHAR(255) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()
