import logging
from typing import TypedDict, Annotated, List, Literal, Dict, Any

# LangChain / LangGraph Imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

# Custom Modules
from chatbot_modules.llm_client import LLMClient
from chatbot_modules.session_manager import SessionManager
from chatbot_modules.recommend_ba import TOOLS_TALK
from chatbot_modules.search_info import TOOLS_INFO
from chatbot_modules.diary_manager import DiaryManager

# Separated Agents
from chatbot_modules.empathy_agent import empathy_node
from chatbot_modules.info_agent import info_node

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangGraph 상태 정의 (메세지, 사용자 정보, 현재 모드)
class AgentState(TypedDict):
    # add_messages: 리스트를 덮어쓰지 않고 append(추가)하는 Reducer 함수
    messages: Annotated[List[BaseMessage], add_messages]
    user_profile: Dict[str, Any]
    current_mode: Literal["chat", "info"]
    seriousness_score: float 


# [Conversaion Engine] 대화의 흐름을 제어하는 메인 클래스
class ConversationEngine:
    def __init__(self):
        self.llm_client = LLMClient()
        self.session_manager = SessionManager()
        self.memory = MemorySaver()
        self.diary_manager = DiaryManager()


        self.app = self._build_graph()
        self.waiting_for_diary_confirm = False # [테스트] 다이어리 생성 대기 플래그 (UI 버튼 시뮬레이션용)

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # 1. Nodes 등록 (분리된 모듈에서 가져온 함수 사용)
        workflow.add_node("empathy_agent", empathy_node)
        workflow.add_node("info_agent", info_node)
        workflow.add_node("tools_talk", ToolNode(TOOLS_TALK))
        workflow.add_node("tools_info", ToolNode(TOOLS_INFO))

        # 2. Edges & Routing
        # Entry Point: 현재 모드에 따라 시작 노드 결정
        workflow.set_conditional_entry_point(
            self._route_mode,
            {"empathy_agent": "empathy_agent", "info_agent": "info_agent"}
        )

        # Empathy Agent -> Tool 사용 여부 확인
        workflow.add_conditional_edges(
            "empathy_agent",
            self._should_continue_talk,
            {"tools_talk": "tools_talk", END: END}
        )
        workflow.add_conditional_edges(
            "info_agent",
            self._should_continue_info,
            {"tools_info": "tools_info", END: END}
        )
        workflow.add_edge("tools_talk", "empathy_agent") # 툴 실행 후 다시 에이전트로 복귀
        workflow.add_edge("tools_info", "info_agent") # 툴 실행 후 다시 에이전트로 복귀
        

        return workflow.compile(checkpointer=self.memory)

    # 라우팅
    def _route_mode(self, state: AgentState):
        """State의 current_mode를 확인하여 경로 분기"""
        mode = state.get("current_mode", "chat")
        if mode == "info":
            return "info_agent"
        return "empathy_agent"

    def _should_continue_talk(self, state: AgentState):
        """Tool Call 존재 여부 확인"""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools_talk"
        return END

    def _should_continue_info(self, state: AgentState):
        """Tool Call 존재 여부 확인"""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools_info"
        return END

    # 다이어리 생성
    def generate_diary_summary(self, user_id: str) -> str:
        """
        오늘의 대화 내용을 요약하여 다이어리를 생성합니다.
        기존에 작성된 다이어리가 있다면 내용을 통합합니다.
        """
        return self.diary_manager.create_diary_for_today(user_id)
    
    # 다이어리 생성 트리거 -> UI상에서 다이어리탭을 누른 것으로 간주
    def _check_diary_trigger(self, text: str) -> bool:
        return text.strip() == "다이어리"

    # Public Interface
    def process_user_message(self, user_id: str, text: str, mode: str = "chat") -> str:
        # --- 다이어리 ---
        # 생성 확인 (Y/N)
        if self.waiting_for_diary_confirm:
            if text.lower() in ['y', 'yes', '네', '응']:
                self.waiting_for_diary_confirm = False
                
                # 생성 전 대화 내용 확인
                chat_history = self.session_manager.export_user_history(user_id)
                if not chat_history or chat_history == "오늘 나눈 대화가 없습니다.":
                    return "오늘 나눈 대화가 없어 다이어리를 생성할 수 없습니다."
                
                return self.generate_diary_summary(user_id)
            else:
                self.waiting_for_diary_confirm = False
                return "다이어리 생성을 취소했습니다. 대화를 계속할까요?"

        # 다이어리 버튼 트리거 확인
        if self._check_diary_trigger(text):
            self.waiting_for_diary_confirm = True
            return "오늘 나눈 대화로 다이어리를 생성할까요? (Y/N)"

        # --- 일반 대화 처리 ---
        session = self.session_manager.load_session(user_id)
        profile = session.get("user_profile", {})
        
        config = {"configurable": {"thread_id": user_id}}
        inputs = {
            "messages": [HumanMessage(content=text)],
            "user_profile": profile,
            "current_mode": mode
        }
        self.session_manager.add_message(user_id, "user", text)

        response_text = ""
        try:
            for event in self.app.stream(inputs, config=config):
                for k, v in event.items():
                    if "messages" in v:
                        msg = v["messages"][-1]
                        if isinstance(msg, AIMessage) and not msg.tool_calls:
                            response_text = msg.content
        except Exception as e:
            logger.error(f"Error: {e}")
            return "오류가 발생했습니다."

        # 대화 저장 (다이어리 소스)
        self.session_manager.add_message(user_id, "assistant", response_text)

        return response_text
    
    
    def process_user_message_stream(self, user_id: str, text: str, mode: str = "chat"):
        # --- 다이어리 ---
        # 생성 확인 (Y/N)
        if self.waiting_for_diary_confirm:
            if text.lower() in ['y', 'yes', '네', '응']:
                self.waiting_for_diary_confirm = False
                
                # 생성 전 대화 내용 확인
                chat_history = self.session_manager.export_user_history(user_id)
                if not chat_history or chat_history == "오늘 나눈 대화가 없습니다.":
                    yield "오늘 나눈 대화가 없어 다이어리를 생성할 수 없습니다."
                    return

                yield self.generate_diary_summary(user_id)
                return
            else:
                self.waiting_for_diary_confirm = False
                yield "다이어리 생성을 취소했습니다. 대화를 계속할까요?"
                return
            
        # 다이어리 버튼 트리거 확인
        if self._check_diary_trigger(text):
            self.waiting_for_diary_confirm = True
            yield "오늘 나눈 대화로 다이어리를 생성할까요? (Y/N)"
            return
        
        # --- 일반 대화 처리 ---
        session = self.session_manager.load_session(user_id)
        profile = session.get("user_profile", {})
        
        config = {"configurable": {"thread_id": user_id}}
        inputs = {
            "messages": [HumanMessage(content=text)],
            "user_profile": profile,
            "current_mode": mode
        }
        
        self.session_manager.add_message(user_id, "user", text)

        full_response = ""
        
        try:
            # 동기 stream 사용 
            for msg, metadata in self.app.stream(inputs, config=config, stream_mode="messages"):
                # 
                if isinstance(msg, AIMessage) and msg.content:
                    token = msg.content
                    full_response += token
                    yield token
                        
        except Exception as e:
            logger.error(f"Streaming Error: {e}")
            yield f"오류가 발생했습니다: {str(e)}"
            return
        
        # 대화 저장 (다이어리 소스)
        if full_response:
            self.session_manager.add_message(user_id, "assistant", full_response)
