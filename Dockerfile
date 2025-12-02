FROM python:3.13-slim
LABEL authors="Jaebeom"

WORKDIR /app

# 필수 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사
COPY . .

ENV PYTHONBUFFERED=1

# 컨테이너 내부 포트
EXPOSE 8000

# uvicorn으로 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]