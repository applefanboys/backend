from App.Api.naverNewsAPI import fetch_news_today

DOMESTIC_KEYWORDS = [
    "코스피",
    "코스닥",
    "국내 증시",
    "장 마감",
    "증시 사항",
]

US_KEYWORDS = [
    "미국 증시",
    "뉴욕증시",
    "나스닥",
    "S&P500",
    "다우지수",
]

STOCK_KEYWORDS = [
    "삼성전자",
    "SK하이닉스",
    "LG에너지솔루션",
    "엔비디아",
    "애플",
    "테슬라",
    "마이크로소프트",
    "구글",
]

ALL_KEYWORDS = DOMESTIC_KEYWORDS + US_KEYWORDS + STOCK_KEYWORDS

def get_today_news():
    all_results = []

    # 키워드별로 따로 호출해서 결과를 쌓음 (사실상 OR 효과)
    for kw in ALL_KEYWORDS:
        rows = fetch_news_today(kw, max_pages=1, display=20)
        all_results.extend(rows)

    # 중복 제거 (origin_url 우선, 없으면 url)
    seen = set()
    merged = []
    for row in all_results:
        key = row.get("origin_url") or row.get("url")
        if key and key not in seen:
            seen.add(key)
            merged.append(row)

    return merged