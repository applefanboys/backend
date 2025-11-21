from typing import List, Dict

class PreferenceRepository:
    """
    나중에 여기에 실제 DB 연동 코드(SQLAlchemy 등)를 넣을 예정.
    지금은 임시로 print만 찍거나, 메모리에 저장하는 식으로 둔다.
    """

    def __init__(self):
        # 임시 메모리 저장소 (user_id -> [category_id, ...])
        self._q1_memory_store: Dict[int, List[int]] = {}
        self._q2_memory_store: Dict[int, List[str]] = {}
        self._q3_memory_store: Dict[int, List[str]] = {}

    # ---------- Q1 ----------
    def save_q1_selection(self, user_id: int, selected_ids: List[int]) -> None:
        # TODO: 실제 DB insert/update 코드로 교체
        self._q1_memory_store[user_id] = selected_ids
        print(f"[DEBUG] Q1 저장 user_id: {user_id}, selected_ids: {selected_ids}")

    def get_q1_selection(self, user_id: int) -> List[int]:
        return self._q1_memory_store.get(user_id, [])

    # ---------- Q2 ----------
    def save_q2_keywords(self, user_id: int, keywords: List[str]) -> None:
        self._q2_memory_store[user_id] = keywords
        print(f"[DEBUG] Q2 저장 user_id={user_id}, keywords={keywords}")

    def get_q2_keywords(self, user_id: int) -> List[str]:
        return self._q2_memory_store.get(user_id, [])

    # ---------- Q3 ----------
    def save_q3_exclude_keywords(self, user_id: int, exclude_keywords: List[str]) -> None:
        self._q3_memory_store[user_id] = exclude_keywords
        print(f"[DEBUG] Q3 저장 user_id={user_id}, exclude_keywords={exclude_keywords}")

    def get_q3_exclude_keywords(self, user_id: int) -> List[str]:
        return self._q3_memory_store.get(user_id, [])

    # ---------- 온보딩 상태 ----------

    def has_q1(self, user_id: int) -> bool:
        return user_id in self._q1_memory_store and len(self._q1_memory_store[user_id]) > 0

    def has_q2(self, user_id: int) -> bool:
        return user_id in self._q2_memory_store and len(self._q2_memory_store[user_id]) > 0

    def has_q3(self, user_id: int) -> bool:
        return user_id in self._q3_memory_store and len(self._q3_memory_store[user_id]) > 0
    # 나중에 DB 붙일 때는 이 부분을:
    #
    # # 세션 가져오기
    # from App.db.session import get_db  # 이런 식으로
    # # SQLAlchemy 모델 import 해서 실제로 INSERT/UPDATE
    #
    #
    # 로 갈아끼우면 됨.