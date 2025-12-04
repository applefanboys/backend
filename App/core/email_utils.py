import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate, formataddr
import os

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

FROM_NAME = "숏뉴스" # 서비스 이름

def send_password_reset_email(to_email: str, token: str):
    reset_link = f"https://api.short-economy/reset-password?token={token}"

    subject = "[숏뉴스] 비밀번호 재설정 링크 안내"
    body = f"""
<html>
      <body>
        <p>안녕하세요.</p>
        <p>아래 버튼을 눌러 비밀번호를 재설정해 주세요.<br>
        (30분 안에만 유효합니다.)</p>

        <p>
          <a href="{reset_link}"
             style="display:inline-block;padding:10px 16px;
                    background-color:#007bff;color:#ffffff;
                    text-decoration:none;border-radius:4px;">
            비밀번호 재설정하기
          </a>
        </p>

        <p>혹시 버튼이 동작하지 않으면 아래 주소를 복사해서 붙여넣기 해 주세요.</p>
        <p>{reset_link}</p>

        <p>본 메일을 요청하지 않으셨다면, 이 메일은 무시하셔도 됩니다.</p>
      </body>
    </html>
"""

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, SMTP_USER))
    msg["To"] = to_email

    # TLS
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
