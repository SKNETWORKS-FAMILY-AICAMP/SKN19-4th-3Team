import logging
import json
from datetime import datetime
from typing import List, Dict

# 기존 모듈 의존성
from chatbot_modules.session_manager import SessionManager
from chatbot_modules.llm_client import LLMClient

logger = logging.getLogger(__name__)

class DiaryManager:
    """
    다이어리 관련 기능을 전담하는 매니저 클래스
    - 다이어리 생성 (LLM 요약)
    - 다이어리 목록 조회
    - 다이어리 삭제
    """
    def __init__(self):
        self.session_manager = SessionManager()
        self.llm_client = LLMClient()

    def create_diary_for_today(self, user_id: str) -> str:
        """
        오늘의 대화를 요약하여 다이어리를 생성 및 저장합니다.
        기존에 작성된 다이어리가 있다면 내용을 통합합니다.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        display_date = datetime.now().strftime("%Y/%m/%d")
        
        # 1. 사용자 정보 및 대화 기록 로드
        session = self.session_manager.load_session(user_id)
        user_name = session["user_profile"].get("name", "회원")
        
        chat_history = self.session_manager.export_user_history(user_id)
        
        # 대화가 없는 경우 처리
        if not chat_history or chat_history == "오늘 나눈 대화가 없습니다.":
            return "오늘 나눈 대화가 없어 다이어리를 생성하지 않았습니다."

        # 기존 다이어리 로드 (통합용)
        existing_diary = self.session_manager.get_diary_entry(user_id, today_str)
        
        # [Fix] 기존 다이어리에서 헤더(날짜/이모지/태그) 제거하고 본문만 추출
        if existing_diary and "\n\n" in existing_diary:
             # 첫 번째 빈 줄 이후가 본문
            parts = existing_diary.split("\n\n", 1)
            # 만약 첫 부분이 헤더 형식([...])이라면 제외
            if parts[0].strip().startswith("["):
                existing_diary = parts[1].strip()
        
        # 2. 프롬프트 구성 (기존 conversation_engine.py의 로직 이관)
        prompt = f"""
        당신은 사용자의 하루를 따뜻하고 아름다운 언어로 기록해주는 '감성 회고록 작가'입니다.
        제공된 [이전 다이어리 내용]과 [오늘의 추가 대화]를 종합하여, 오늘 하루를 정리하는 **하나의 완성된 에세이**를 작성해주세요.
        대화 내용을 분석하여 다음 3가지 요소를 포함한 **JSON 형식**으로만 답변하세요.

        [분석 대상]
        사용자: {user_name}
        대화 내용: {chat_history}
        (기존 내용이 있다면 통합하세요: {existing_diary})

        [작성 규칙]
        1. summary:
           - 사용자의 하루 기분과 활동을 **2~3문장**으로 짧고 따뜻하게 요약하세요.
           - 문장 사이에는 줄바꿈(\\n\\n)을 넣으세요.
           - 3인칭 관찰자 시점("~하셨어요")을 사용하세요.
        2. keywords:
           - 오늘의 핵심 단어(감정, 활동 등)를 1~3개 뽑아 리스트로 만드세요.
        3. emoji:
           - keywords를 기반으로, 오늘 하루의 분위기를 가장 잘 나타내는 **이모지 1개**를 선택하세요.

        4. **어조 및 태도:**
           - 사용자를 '{user_name}님'이라고 지칭하며, 곁에서 지켜본 동반자가 사용자의 하루를 따뜻하게 회고하는듯한 어조(~했어요, ~했답니다)를 사용하세요.
           - 단순한 사실 나열("밥을 먹었다")보다는, 그 순간의 **감정과 의미**("따뜻한 밥 한 끼로 마음을 채우셨어요")에 집중하세요.
           - 삶의 마지막을 준비하거나 외로움을 느끼는 분들에게 위로와 평온함을 줄 수 있도록 부드럽고 품격 있는 문체를 유지하세요.

        5. **내용 통합:**
           - [이전 다이어리 내용]이 있다면, [오늘의 추가 대화]와 자연스럽게 연결하여 하나의 흐름으로 만드세요. (내용 중복 금지)
           - 사용자가 느꼈던 주요 감정(우울, 기쁨, 평온 등)과 그에 대한 챗봇의 공감, 추천받은 활동, 사용자의 반응을 중심으로 서술하세요.
           - 마지막 문장은 내일에 대한 잔잔한 희망이나, 오늘 밤의 평안을 비는 문구로 마무리하세요.

        [출력 예시]
        {{
            "emoji": "🍵",
            "keywords": ["평온", "차한잔"],
            "summary": "비 오는 창밖을 보며 차 한 잔을 드셨어요.\\n\\n마음이 한결 차분해지셨다고 하셨습니다.\\n\\n이러한 에너지가 밝은 내일을 만들어가길 바랍니다."
        }}
        """

        # 3. LLM 생성 및 파싱
        raw_response = self.llm_client.generate_text("JSON 형식으로만 답변하세요.", prompt)
        
        try:
            cleaned_response = raw_response.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            
            emoji = data.get("emoji", "📝")
            keywords = data.get("keywords", [])
            summary = data.get("summary", "")
            
            tags = " ".join([f"#{k}" for k in keywords])
            
            final_diary = f"[{display_date}] {emoji} {tags}\n\n{summary}"
            
        except Exception as e:
            logger.error(f"다이어리 생성 중 JSON 파싱 실패: {e}")
            final_diary = f"[{display_date}] 📝 #기록\n\n{raw_response}"

        # 4. 저장
        self.session_manager.save_diary_entry(user_id, today_str, final_diary)
        logger.info(f"다이어리 생성 완료: {user_id}, {today_str}")
        
        return final_diary

    def list_diaries(self, user_id: str) -> List[Dict[str, str]]:
        """
        사용자의 다이어리 목록 반환 (날짜, 이모지, 태그 등)
        """
        return self.session_manager.get_all_diaries_metadata(user_id)

    def delete_diary(self, user_id: str, date_str: str) -> str:
        """
        특정 날짜의 다이어리 삭제
        date_str 형식: YYYY-MM-DD
        """
        success = self.session_manager.delete_diary_entry(user_id, date_str)
        if success:
            return f"[{date_str}] 다이어리가 삭제되었습니다."
        else:
            return f"[{date_str}] 삭제할 다이어리가 없거나 오류가 발생했습니다."