from typing import List, Dict
from App.repository.naverNewsRepo import get_today_news
# API 호출 함수 직접 import (개별 키워드 검색용)
from App.api.naverNewsAPI import fetch_news_today

# 기존 함수 (전체 뉴스)
def get_today_economy_news():
    return get_today_news()

# [추가됨] 사용자 맞춤 뉴스 검색
def get_personalized_news(keywords: List[str]) -> List[Dict]:
    """
    사용자가 설정한 키워드 리스트를 받아,
    각 키워드별로 뉴스를 검색한 뒤 합쳐서 반환합니다.
    """
    if not keywords:
        # 키워드가 없으면 기본(전체) 뉴스를 반환합니다.
        print("키워드가 없어 전체 뉴스를 반환합니다.")
        return get_today_news()

    all_results = []
    
    print(f"검색할 키워드 목록: {keywords}")

    # 각 키워드별로 뉴스 검색
    for kw in keywords:
        # fetch_news_today: API 직접 호출
        # 속도를 위해 max_pages=1, display=5 정도로 제한
        rows = fetch_news_today(kw, max_pages=1, display=5)
        all_results.extend(rows)

    # 중복 제거 (여러 키워드에 같은 뉴스가 걸릴 수 있음)
    seen = set()
    merged = []
    for row in all_results:
        # origin_url이 같으면 같은 뉴스로 취급
        key = row.get("origin_url") or row.get("url")
        if key and key not in seen:
            seen.add(key)
            merged.append(row)

    print(f"총 {len(merged)}개의 맞춤 뉴스가 검색되었습니다.")
    return merged