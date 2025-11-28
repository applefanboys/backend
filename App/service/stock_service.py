import os
import json
import random
import traceback
from datetime import datetime, timedelta
from openai import OpenAI
import FinanceDataReader as fdr


class StockService:
    def __init__(self):
        # 👇 여기에 팀장님 키(sk-...)를 꼭 다시 넣으세요!
        self.api_key = "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"

        if self.api_key and len(self.api_key) > 10:
            print(f"🔑 API 키 장전 완료: {self.api_key[:5]}...")
        else:
            print("❌ API 키가 없거나 너무 짧습니다!")

        self.client = OpenAI(api_key=self.api_key)
        self.model_name = "gpt-4o-mini"

    async def get_recommendation(self, user_data: dict):
        print("\n" + "=" * 50)
        print("🚀 [디버깅] 주식 추천 로직 시작")

        try:
            # 1. 주제 선정
            target_topic = "경제"
            if user_data.get("keywords"):
                target_topic = random.choice(user_data["keywords"])
            elif user_data.get("categories"):
                target_topic = random.choice(user_data["categories"])

            print(f"🎯 주제: {target_topic}")

            # 2. OpenAI 1차 질문 (프롬프트 강화)
            search_prompt = f"""
            한국 주식 시장에서 '{target_topic}' 관련 대장주 3개만 JSON으로 알려줘.

            [중요]
            1. 무조건 리스트([]) 형태로만 대답해. 딕셔너리 key 쓰지 마.
            2. 종목명은 'name', 종목코드는 'code'라는 영어 key를 사용해.
            3. 코드는 6자리 숫자여야 해.

            예시: [{{"name": "삼성전자", "code": "005930"}}, {{"name": "SK하이닉스", "code": "000660"}}]
            """

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "JSON 형식으로만 대답해."},
                    {"role": "user", "content": search_prompt}
                ],
                temperature=0.3  # 창의성 좀 낮춰서 형식 잘 지키게 함
            )

            ai_text = response.choices[0].message.content
            cleaned_search = ai_text.replace("```json", "").replace("```", "").strip()

            try:
                candidates = json.loads(cleaned_search)
                print(f"📋 AI 원본 응답 파싱: {candidates}")

                # 🔥 [안전장치 1] AI가 딕셔너리로 감싸서 줬을 경우 (예: {'stocks': [...]})
                if isinstance(candidates, dict):
                    print("⚠️ 딕셔너리가 감지됨! 내부 리스트 탐색 중...")
                    for key, value in candidates.items():
                        if isinstance(value, list):
                            candidates = value
                            print(f"   -> 리스트 발견! ({key})")
                            break
                    else:
                        # 리스트 못 찾았으면 강제로 1개라도 만듦
                        candidates = [candidates]

            except:
                print(f"⚠️ JSON 파싱 실패, 기본값 사용")
                candidates = [{"name": "KODEX 200", "code": "069500"}]

            # 3. 데이터 수집
            candidates_data_str = ""
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
            valid_candidates = []

            for stock in candidates:
                name = "Unknown"
                code = "000000"

                try:
                    if isinstance(stock, dict):
                        # 🔥 [안전장치 2] 한글/영어 키 모두 지원
                        code = str(stock.get("code") or stock.get("코드") or "").zfill(6)
                        name = stock.get("name") or stock.get("이름") or "Unknown"

                        # 코드가 없으면 패스
                        if code == "000000" or not code:
                            print(f"   ⚠️ 종목 코드 없음: {stock}")
                            continue
                    else:
                        print(f"   ⚠️ 데이터 형식이 이상함: {stock}")
                        continue

                    print(f"   Running FDR... {name}({code})")
                    df = fdr.DataReader(code, start_date, end_date)

                    if not df.empty:
                        start_p = int(df.iloc[0]['Close'])
                        end_p = int(df.iloc[-1]['Close'])
                        change = ((end_p - start_p) / start_p) * 100
                        candidates_data_str += f"- {name}({code}): {change:.2f}% 변동\n"
                        valid_candidates.append(name)
                    else:
                        print(f"   ⚠️ 데이터 없음: {name}")

                except Exception as e:
                    print(f"   ⚠️ FDR 에러 ({name}): {e}")
                    continue

            if not valid_candidates:
                print("🚨 유효한 종목 없음 -> 분석 중단")
                return {
                    "user_interest": target_topic,
                    "candidates_found": [],
                    "ai_result": {
                        "recommended_stock": "추천 불가",
                        "stock_code": "",
                        "reason": "AI가 찾은 종목들의 데이터를 불러올 수 없습니다."
                    }
                }

            # 4. 최종 분석
            analyze_prompt = f"""
            주제: '{target_topic}'
            데이터:
            {candidates_data_str}

            가장 투자 매력도가 높은 종목 1개를 추천해줘.
            반드시 아래 JSON 형식으로만 대답해.
            {{
                "recommended_stock": "종목명",
                "stock_code": "종목코드",
                "reason": "이유..."
            }}
            """

            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "JSON으로만 대답해."},
                    {"role": "user", "content": analyze_prompt}
                ]
            )

            final_text = final_response.choices[0].message.content
            cleaned_final = final_text.replace("```json", "").replace("```", "").strip()
            final_json = json.loads(cleaned_final)

            print("🎉 [디버깅 종료] 모든 과정 성공!")
            print("=" * 50 + "\n")

            return {
                "user_interest": target_topic,
                "candidates_found": valid_candidates,
                "ai_result": final_json
            }

        except Exception as e:
            print("\n" + "!" * 50)
            print(f"🚨 [치명적 에러] {e}")
            print(traceback.format_exc())
            print("!" * 50 + "\n")
            raise e


stock_service = StockService()