from typing import List, Optional, Sequence
import random
import os
import json
import random
from typing import List, Optional, Sequence
from openai import OpenAI
from datetime import datetime

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
today = datetime.now().strftime("%Y-%m-%d")

def ai_generate_keywords_with_openai(
    q1_categories: List[int],
    q2_keywords: List[str],
    q3_excluded: List[str],
    target_size: int = 6,
) -> List[str]:
    """
    OpenAI API를 사용해서 Q1/Q2/Q3 기반 오늘의 키워드 추천.
    JSON 배열 형태로만 받도록 프롬프트 강제.
    """

    prompt = f"""
오늘 날짜: {today}

너는 한국어 경제 뉴스 추천 시스템의 키워드 분석 AI야.

다음은 사용자의 경제 뉴스 취향 정보야:

- Q1 선택 카테고리 ID 리스트: {q1_categories}
- Q2 선호 키워드: {q2_keywords}
- Q3 제외(보기 싫은) 키워드: {q3_excluded}

요구사항:

1. 사용자의 Q1, Q2를 바탕으로 오늘 읽으면 좋을 경제/투자 관련 주요 키워드 {target_size}개를 추천해.
2. Q3 제외 키워드는 절대 포함하지 마.
3. 초보 투자자 기준으로 너무 어려운 전문 용어는 피하고, 실제 뉴스 헤드라인에 자주 등장할 법한 단어들로 구성해.
4. **반드시 JSON 리스트 형식으로만 출력해.** 설명 문장 쓰지 말고, 예시는 다음과 같아:
5. **오늘 날짜({today})를 기준으로**, 오늘의 경제 상황에 맞춰 주요 키워드 {target_size}개를 추천해.
6. 같은 날짜에는 비슷한 추천을 유지하되, 날짜가 바뀌면 새로운 키워드 조합을 생성해.

[
  "코스피",
  "환율",
  "미국증시",
  "금리",
  "반도체",
  "인플레이션"
]
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",   # 프로젝트에서 쓰는 모델 이름에 맞춰 바꿔도 됨
            input=prompt,
        )

        # responses API 구조에서 텍스트 꺼내기
        text = response.output[0].content[0].text.strip()

        # JSON 파싱
        keywords = json.loads(text)

        if not isinstance(keywords, list):
            raise ValueError("OpenAI 응답이 리스트가 아님")

        # 문자열만 남기기 + strip
        keywords = [str(k).strip() for k in keywords]

        # Q3 제외 키워드 한 번 더 필터링
        keywords = [k for k in keywords if k not in q3_excluded]

        # target_size 만큼 자르기
        return keywords[:target_size]

    except Exception as e:
        print(f"[AI Keyword Error - OpenAI] {e}")
        return []  # 실패 시 빈 리스트 → fallback 용

# Q1 카테고리 id 기준 추천 키워드 매핑 (예시)
CATEGORY_KEYWORDS_BY_ID = {
    1: ["금리", "물가", "성장률", "환율", "GDP"],              # 전체 경제
    2: ["주식시장", "코스피", "코스닥", "반도체", "2차전지"],  # 주식·증권
    3: ["부동산", "전세", "월세", "매매", "청약"],              # 부동산
    4: ["재테크", "ETF", "펀드", "대출", "저축"],              # 금융상품
    5: ["미국증시", "나스닥", "S&P500", "테슬라", "애플"],      # 해외·글로벌
    6: ["원자재", "유가", "금", "구리", "원유"],               # 원자재·에너지
    7: ["환율", "달러", "엔화", "위안화", "유로"],             # 환율·외환
    8: ["거시경제", "통화정책", "재정정책", "경기침체", "인플레이션"], # 거시·정책
}

# 전체 fallback 풀 (부족할 때 채우는 용도)
GLOBAL_KEYWORDS_POOL = list({
    kw for kws in CATEGORY_KEYWORDS_BY_ID.values() for kw in kws
})

def rule_based_recommend(
    q1_categories: Optional[Sequence[int]],
    q2_keywords: Optional[Sequence[str]],
    q3_keywords: Optional[Sequence[str]],
    target_size: int = 6,
) -> List[str]:
    # None 방어
    q1_categories = list(q1_categories or [])
    q2_keywords   = list(q2_keywords   or [])
    q3_keywords   = list(q3_keywords   or [])

    result: List[str] = []

    # 1) Q2: 사용자가 직접 적은 키워드 최우선
    result.extend(q2_keywords)

    # 2) Q1: 선택한 카테고리별 대표 키워드 랜덤 추가
    for cat_id in q1_categories:
        if cat_id in CATEGORY_KEYWORDS_BY_ID:
            candidates = CATEGORY_KEYWORDS_BY_ID[cat_id]
            # 너무 많이 뽑지 말고 1~2개 정도
            k = 2 if len(candidates) >= 2 else 1
            sampled = random.sample(candidates, k=k)
            result.extend(sampled)

    # 3) 중복 제거 (순서 유지)
    result = list(dict.fromkeys(result))

    # 4) Q3: 제외 키워드 제거
    result = [kw for kw in result if kw not in q3_keywords]

    # 5) 아직 target_size 개수보다 적으면, 글로벌 풀에서 채우기
    if len(result) < target_size:
        # 이미 사용/제외된 키워드 빼고 후보 생성
        candidates = [
            kw for kw in GLOBAL_KEYWORDS_POOL
            if kw not in result and kw not in q3_keywords
        ]
        random.shuffle(candidates)
        need = target_size - len(result)
        result.extend(candidates[:need])

    # 6) 최종적으로 딱 target_size개만 반환
    return result[:target_size]

def generate_today_keywords(
    q1_categories: Optional[Sequence[int]],
    q2_keywords: Optional[Sequence[str]],
    q3_keywords: Optional[Sequence[str]],
    target_size: int = 6,
) -> List[str]:
    q1_categories = list(q1_categories or [])
    q2_keywords   = list(q2_keywords   or [])
    q3_keywords   = list(q3_keywords   or [])

    # 1) OpenAI로 먼저 시도
    ai_result = ai_generate_keywords_with_openai(
        q1_categories=q1_categories,
        q2_keywords=q2_keywords,
        q3_excluded=q3_keywords,
        target_size=target_size,
    )

    if len(ai_result) >= target_size:
        return ai_result[:target_size]

    # 2) 부족하면 규칙 기반으로 채우기
    print("[Keyword] AI 결과 부족 → rule-based fallback 실행")
    return rule_based_recommend(
        q1_categories=q1_categories,
        q2_keywords=q2_keywords,
        q3_keywords=q3_keywords,
        target_size=target_size,
    )

