# 1. 파이썬 3.10 버전을 기반으로 시작
FROM python:3.10-slim

# 2. 컨테이너 안의 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 목록 파일을 먼저 복사
COPY requirements.txt .

# 4. 라이브러리 설치 (gtts 포함)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 코드 파일들 복사
COPY .. .

# 6. 서버가 8000번 포트를 사용할 거라고 알려줌
EXPOSE 8000

# 7. 컨테이너가 시작될 때 실행할 명령 (서버 구동)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]