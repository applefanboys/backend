import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate, formataddr
import os

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

FROM_NAME = "숏뉴스" # 서비스 이름

# 앱 딥링크 스킴을 사용하는 걸로 변경함.(기존엔 웹)
APP_DEEPLINK_SCHEME = os.getenv("APP_DEEPLINK_SCHEME", "shortnews")
APP_DEEPLINK_HOST = os.getenv("APP_DEEPLINK_HOST", "reset-password")

def send_password_reset_email(to_email: str, token: str):
    # shortnews://reset-password?token=xxxx 형태
    reset_link = f"{APP_DEEPLINK_SCHEME}://{APP_DEEPLINK_HOST}?token={token}"

    subject = "[숏뉴스] 비밀번호 재설정 링크 안내"
    body = f"""
안녕하세요.

아래 링크를 클릭해서 비밀번호를 재설정해주세요.
(30분 안에만 유효합니다.)

{reset_link}

본 메일을 요청하지 않으셨다면, 이 메일은 무시하셔도 됩니다.
"""

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, SMTP_USER))
    msg["To"] = to_email

    # TLS
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
