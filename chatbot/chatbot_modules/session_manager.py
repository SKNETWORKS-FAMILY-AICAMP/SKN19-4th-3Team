import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionManager:
    """
    사용자 세션 및 기록 관리 (UUID 기반 / 날짜별 분리 저장)

    디렉터리 구조 예시:
      chatbot/sessions/{user_id}/
        ├── profile.json           # 사용자 프로필, 마지막 방문일 등
        ├── history/
        │    └── 2025-12-06.json   # 해당 날짜 대화 내역
        └── diaries/
             └── 2025-12-06.txt    # 다이어리 텍스트
    """

    def __init__(self, storage_path: str = "chatbot/sessions"):
        self.storage_path = storage_path
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    # ----------------------------------------------------------------------
    # 내부 경로 유틸
    # ----------------------------------------------------------------------
    def generate_user_id(self) -> str:
        """새로운 사용자 UUID 생성"""
        return str(uuid.uuid4())

    def _get_user_dir(self, user_id: str) -> str:
        user_dir = os.path.join(self.storage_path, user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir

    def _get_profile_path(self, user_id: str) -> str:
        return os.path.join(self._get_user_dir(user_id), "profile.json")

    def _get_history_path(self, user_id: str, date_str: Optional[str] = None) -> str:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        history_dir = os.path.join(self._get_user_dir(user_id), "history")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        return os.path.join(history_dir, f"{date_str}.json")

    def _get_diary_path(self, user_id: str, date_str: str) -> str:
        diary_dir = os.path.join(self._get_user_dir(user_id), "diaries")
        if not os.path.exists(diary_dir):
            os.makedirs(diary_dir)
        return os.path.join(diary_dir, f"{date_str}.txt")

    # ----------------------------------------------------------------------
    # 세션 로드 / 저장
    # ----------------------------------------------------------------------
    def load_session(self, user_id: str) -> Dict[str, Any]:
        """
        세션 로드 (프로필 + 오늘 대화 내용)

        - profile.json 에서 user_profile / last_visit 로드
        - 오늘 날짜 history/{YYYY-MM-DD}.json 에서 대화 내역 로드
        """
        # 기본 세션 구조
        session_data: Dict[str, Any] = {
            "user_id": user_id,
            "last_visit": None,
            "user_profile": {
                "name": "사용자",
                "age": "미상",
                "mobility": "거동 가능",
                "family": "정보 없음",
            },
            "conversation_history": [],
        }

        # 1) 프로필 로드
        profile_path = self._get_profile_path(user_id)
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    session_data.update(profile_data)
            except Exception as e:
                logger.error(f"프로필 로드 실패: {e}")

        # 2) 오늘 히스토리 로드
        history_path = self._get_history_path(user_id)
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
                    session_data["conversation_history"] = history_data.get(
                        "messages", []
                    )
            except Exception as e:
                logger.error(f"대화 내역 로드 실패: {e}")

        return session_data

    def save_profile(self, user_id: str, data: Dict[str, Any]):
        """
        프로필 저장 (last_visit, user_profile만 저장)

        history 정보는 별도 파일에 저장해서 profile.json 이 비대해지지 않도록 한다.
        """
        profile_path = self._get_profile_path(user_id)

        save_data = {
            "user_id": user_id,
            "last_visit": data.get("last_visit"),
            "user_profile": data.get("user_profile", {}),
        }

        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"프로필 저장 실패: {e}")

    def save_history(self, user_id: str, messages: List[Dict[str, Any]]):
        """오늘 대화 내역 저장 (덮어쓰기)"""
        history_path = self._get_history_path(user_id)
        data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "messages": messages,
        }
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"대화 내역 저장 실패: {e}")

    def save_session(self, user_id: str, data: Dict[str, Any]):
        """
        [Wrapper] 전체 세션 데이터를 받아서
        - 프로필
        - 오늘 히스토리
        를 각각 파일로 나누어 저장.
        """
        self.save_profile(user_id, data)
        if "conversation_history" in data:
            self.save_history(user_id, data["conversation_history"])

    # ----------------------------------------------------------------------
    # 대화 기록 관리
    # ----------------------------------------------------------------------
    def add_message(self, user_id: str, role: str, content: str):
        """
        대화 기록 추가 (오늘 날짜 기준)

        - role: "user" 또는 "assistant"
        - content: 메시지 텍스트
        """
        history_path = self._get_history_path(user_id)
        messages: List[Dict[str, Any]] = []

        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
            except Exception:
                # 파일이 깨져 있거나 파싱 실패 시, 새로 시작
                messages = []

        message_entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }
        messages.append(message_entry)
        self.save_history(user_id, messages)

    def update_last_visit(self, user_id: str):
        """종료 시 방문 시간 업데이트"""
        session = self.load_session(user_id)
        session["last_visit"] = datetime.now().isoformat()
        self.save_profile(user_id, session)

    # ----------------------------------------------------------------------
    # 환영 메시지 & 히스토리 export
    # ----------------------------------------------------------------------
    def get_welcome_message(self, user_id: str) -> str:
        """
        환영 인사 생성.

        - 첫 방문: "안녕하세요, ..."
        - 같은 날 재방문: "다시 오셨군요..."
        - 1일 경과: "밤사이 편안하셨나요?"
        - 그 이상: "다시 뵙게 되어 반갑습니다."
        """
        session = self.load_session(user_id)
        name = session.get("user_profile", {}).get("name", "")
        last_visit_str = session.get("last_visit")

        title = f"{name}님" if name and name != "사용자" else "회원님"

        if not last_visit_str:
            return f"안녕하세요, {title}. 오늘은 좀 어떠신가요?"

        try:
            days_diff = (datetime.now() - datetime.fromisoformat(last_visit_str)).days
            if days_diff == 0:
                return "다시 오셨군요. 이야기를 계속 나눠볼까요?"
            elif days_diff == 1:
                return f"{title}, 밤사이 편안하셨나요?"
            else:
                return f"{title}, 다시 뵙게 되어 반갑습니다."
        except Exception:
            return f"안녕하세요, {title}."

    def export_user_history(self, user_id: str) -> str:
        """
        오늘의 대화 기록 내보내기 (다이어리용 문자열)

        - 포맷: [HH:MM] 나/AI: 내용
        """
        history_path = self._get_history_path(user_id)
        messages: List[Dict[str, Any]] = []

        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
            except Exception:
                messages = []

        lines: List[str] = []
        for msg in messages:
            role = "나" if msg["role"] == "user" else "AI"
            time = msg["timestamp"][11:16]  # HH:MM
            lines.append(f"[{time}] {role}: {msg['content']}")

        return "\n".join(lines) if lines else "오늘 나눈 대화가 없습니다."

    # ----------------------------------------------------------------------
    # 다이어리 파일 관리
    # ----------------------------------------------------------------------
    def get_diary_entry(self, user_id: str, date_str: str) -> str:
        """해당 날짜의 다이어리 원본 텍스트 로드"""
        path = self._get_diary_path(user_id, date_str)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def save_diary_entry(self, user_id: str, date_str: str, content: str):
        """다이어리 저장 (덮어쓰기)"""
        path = self._get_diary_path(user_id, date_str)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def delete_diary_entry(self, user_id: str, date_str: str) -> bool:
        """다이어리 삭제"""
        path = self._get_diary_path(user_id, date_str)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"다이어리 삭제 완료: {path}")
                return True
            except Exception as e:
                logger.error(f"다이어리 삭제 중 오류: {e}")
                return False
        return False

    def get_all_diaries_metadata(self, user_id: str) -> List[Dict[str, str]]:
        """
        캘린더 UI용 다이어리 메타데이터 목록 추출.

        반환 예시:
        [
          {
            "date": "2025-12-06",
            "emoji": "📝",
            "tags": "#행복 #가족",
            "preview": "오늘은 가족들과 함께..."
          },
          ...
        ]
        """
        diary_dir = os.path.join(self._get_user_dir(user_id), "diaries")
        if not os.path.exists(diary_dir):
            return []

        diary_files = glob.glob(os.path.join(diary_dir, "*.txt"))
        metadata_list: List[Dict[str, str]] = []

        for file_path in diary_files:
            try:
                filename = os.path.basename(file_path)
                date_part = filename.replace(".txt", "")

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                    first_line = lines[0] if lines else ""
                    emoji = "📝"
                    tags = ""

                    if "]" in first_line:
                        parts = first_line.split("]", 1)
                        meta_part = parts[1].strip()
                        tokens = meta_part.split()
                        if tokens:
                            emoji = tokens[0]
                            tags = " ".join(
                                [t for t in tokens if t.startswith("#")]
                            )

                    metadata_list.append(
                        {
                            "date": date_part,
                            "emoji": emoji,
                            "tags": tags,
                            "preview": (content[:50] + "..."),
                        }
                    )
            except Exception as e:
                logger.error(
                    f"다이어리 메타데이터 파싱 실패 ({file_path}): {e}"
                )
                continue

        metadata_list.sort(key=lambda x: x["date"])
        return metadata_list
