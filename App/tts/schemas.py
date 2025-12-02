from pydantic import BaseModel

class ShortformTTSRequest(BaseModel):
    """
    그냥 임의의 뉴스 텍스트를 숏폼 음성으로 듣고 싶을 때 사용
    (주요 뉴스, AI 요약 뉴스 등 아무 텍스트나 가능)
    """
    # 뉴스 원문 or 요약본 (어디서 온 뉴스든 상관 없음)
    text: str

    # 필요하면 조절 가능(글자수 기준, 10~30초용 대략)
    max_chars: int = 180

    # 추후 감정/톤 조절하고 싶으면 이런 필드도 추가 가능
    # style: str | None = None

class PersonalizedShortformTTSRequest(BaseModel):
    """
    사용자 맞춤형 숏폼 뉴스 TTS.
    user_id로 선호도/온보딩 정보를 찾아서,
    그에 맞는 기사를 고른 뒤 음성으로 읽어줌.
    """
    user_id: int
    # 나중에 'ai', 'major', 'both' 이런 식으로 소스를 나누고 싶으면 추가
    # source: Literal["ai", "major", "both"] = "both"
    max_chars: int = 180