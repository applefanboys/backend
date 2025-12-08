# App/tts/routes.py
import base64

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from App.core.database import get_db

from .schemas import (
    ShortformTTSRequest,
    PersonalizedShortformTTSRequest,
)
from .service import (
    generate_shortform_script,
    tts_stream,
    build_personalized_news_text,
    extract_og_image,
)

router = APIRouter(
    prefix="/api/tts",
    tags=["tts"]
)

# 1) 일반 숏폼 TTS (주요 뉴스 / AI 요약 등 아무 텍스트)
@router.post("/shortform")
def shortform_tts(req: ShortformTTSRequest):
    if not req.text.strip():
        raise HTTPException(400, "text가 비어 있습니다.")

    # 실제로 읽을 스크립트 생성
    script = generate_shortform_script(
        original_text=req.text,
        max_chars=req.max_chars
    )

    encoded_script = base64.b64encode(script.encode("utf-8")).decode("ascii")

    # 이미지 URL 결정 로직
    image_url = None

    # 1) 요청에 image_url이 직접 온 경우 → 그대로 사용
    if req.image_url:
        image_url = req.image_url

    # 2) image_url은 없고 origin_url만 온 경우 → OG 이미지 추출
    elif req.origin_url:
        image_url = extract_og_image(req.origin_url)

    # 헤더 구성
    headers = {
        "Content-Disposition": 'inline; filename="shortform_news.mp3"',
        "X-TTS-Text": encoded_script,
    }
    if image_url:
        headers["X-Image-Url"] = image_url

    return StreamingResponse(
        tts_stream(script),
        media_type="audio/mpeg",
        headers=headers,
    )


# 2) 사용자 맞춤형 숏폼 TTS (온보딩 + 네이버 API)
@router.post("/shortform/personalized")
def personalized_shortform_tts(
    req: PersonalizedShortformTTSRequest,
    db: Session = Depends(get_db),
):
    try:
        # (1) 온보딩 + 네이버 API 기반으로 유저 맞춤형 뉴스 텍스트 만들기
        news = build_personalized_news_text(db, req.user_id)

        base_text = news["base_text"]
        image_url = news.get("image_url") or ""

        # (2) 그 텍스트를 10~30초용 숏폼 스크립트로 요약
        script = generate_shortform_script(
            original_text=base_text,
            max_chars=req.max_chars
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 디버깅용 로그 찍고 적당히 메시지 감싸기
        raise HTTPException(status_code=500, detail="맞춤형 뉴스 생성 중 오류가 발생했습니다.")

    encoded_script = base64.b64encode(script.encode("utf-8")).decode("ascii")

    headers = {
        "Content-Disposition": 'inline; filename="personalized_shortform_news.mp3"',
        "X-TTS-Text": encoded_script,
    }
    if image_url:
        headers["X-Image-Url"] = image_url

    # (3) TTS로 스트리밍 응답
    return StreamingResponse(
        tts_stream(script),
        media_type="audio/mpeg",
        headers=headers,
    )
