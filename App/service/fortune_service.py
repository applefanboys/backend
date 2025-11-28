import json
import os
from platform import system
from typing import List, Optional

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_today_fortune(
        name: Optional[str] = None,
        birthdate: Optional[str] = None,    # "2002-08-05" 형식 등
        interests: Optional[List[str]] = None,
        sign: Optional[str] = None,     # 별자리/띠
) -> dict:
    """
    OpenAI API를 사용해서 오늘의 운세를 JSON 형태로 생성해주는 함수.
    """
    if interests is None:
        interests = []

    profile_text = f"""이름: {name or "비공개"}
생년월일: {birthdate or "비공개"}
관심사: {", ".join(interests) if interests else "비공개"}
별자리/띠: {sign or "비공개"}"""

    system_prompt = (
        "너는 한국어로 오늘의 운세를 알려주는 전문가야. "
        "부드럽고 현실적인 조언 위주로 운세를 말해줘."
    )

    user_prompt = f"""
    다음 [사용자 정보]를 참고해서, 오늘 하루 기준으로 운세를 작성해줘.


[사용자 정보]
{profile_text}

[작성 규칙]
- 너무 무섭거나 부정적인 내용은 피하고, 부드러운 조언 위주로 써.
- 각 항목은 2~3문장 정도로.
- 말투는 친근하지만 반말은 쓰지 마.
- 오늘 하루 기준으로만 이야기해.

[출력 형식]
반드시 아래 JSON 형식 그대로만 출력해. 한국어로 작성해.

{{
"overall": "오늘 하루 전반적인 운세를 2~3문장으로 설명",
"money": "금전/재물 관련 운세",
"love": "연애/대인관계 운세",
"work_study": "공부/일/진로 관련 운세",
"health": "건강/컨디션 관련 운세",
"lucky_item": "오늘의 행운 아이템 한 가지",
"lucky_color": "오늘의 행운 색깔 한 가지",
"summary_keywords": ["키워드1", "키워드2", "키워드3"]
}}

위 JSON 이외의 다른 텍스트(설명, 인사말 등)는 절대 쓰지 마.
"""
    completion = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    raw_text = completion.choices[0].message.content


    #JSON 파싱
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # 혹시 JSON이 살짝 깨져도 서버가 안 터지게 fallback
        data = {
            "overall": raw_text.strip(),
            "money": "",
            "love": "",
            "work_study": "",
            "health": "",
            "lucky_item": "",
            "lucky_color": "",
            "summary_keywords": [],
        }

    return data