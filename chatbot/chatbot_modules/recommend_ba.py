import os
import json
import logging
import random
# Pinecone & LangChain
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from dotenv import load_dotenv
load_dotenv()

# 연결 상태 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tavily 클라이언트 (직접 도구로 쓰지 않고 내부 호출용으로 사용)
_tavily_client = TavilySearch(max_results=3)

@tool
def search_from_web_tool(query: str) -> str:
    """
    [Tool] 웹 검색 도구입니다. **구체적인 사실(Fact)**을 찾을 때만 사용하세요.

    [사용 가능한 상황]
    1. **실시간 정보**: 오늘 날씨, 최신 뉴스, 현재 트렌드.
    2. **구체적 해결책**: "잠 잘 오는 법", "소화 잘 되는 자세" 등 검증된 팁(Tip).
    3. **추억 회상 보조 (중요)**: 사용자가 노래 제목, 가사, 영화/드라마 제목, 연예인 이름, 과거의 특정 사건 등을 물어볼 때.
       - 예: "그 노래 가사가 뭐였지?", "감자별 OST 제목이 뭐야?", "90년대 유행했던 드라마"
       - **주의**: 환자의 기억이 흐릿할 수 있으므로, 반드시 검색을 통해 **정확한 사실**을 확인하고 답변해야 합니다.

    [절대 사용 금지 (Strictly Forbidden)]
    - **철학적인 질문**: "죽음이란 무엇인가", "삶의 의미는 무엇인가", "왜 사는가" 등 정답이 없는 질문에는 **절대 사용하지 마세요**.
      - 이런 질문에는 반드시 **`search_welldying_wisdom_tool`**을 사용해야 합니다.
    - **단순 위로**: 정보가 필요 없는 감정적 호소에는 도구를 사용하지 마세요.
    """
    print(f"[Tool: 검색 요청] 검색어: {query}")
    try:
        result = _tavily_client.invoke(query)
        print(f"[Tool: 검색 결과] {result}")
        return result
    except Exception as e:
        print(f"[Tool: 검색 오류] {e}")
        return f"검색 중 오류가 발생했습니다: {e}"

# 데이터 파일 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, '..', 'data', 'conversation_rules.json')

# 설정
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TALK_INDEX_NAME = "talk-assets"
WISDOM_INDEX_NAME = "welldying-wisdom"
EMBEDDING_MODEL = "text-embedding-3-small"

# 전역 객체 초기화
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
except Exception as e:
    logger.warning(f"Pinecone 초기화 실패: {e}")
    index = None

# 대화 규칙
with open(file_path, 'r', encoding='utf-8') as f:
    RULES = json.load(f)

@tool
def recommend_activities_tool(user_emotion: str, mobility_status: str = "거동 가능") -> str:
    """
    [Tool] 사용자의 감정과 거동 상태를 기반으로 '의미 있는 활동'을 추천합니다.
    사용자가 심심해하거나, 무기력하거나, 기분 전환이 필요할 때 호출하세요.

    [사용해야 하는 상황]
    - 사용자가 "심심해", "무기력해", "오늘 뭐 하지?"라고 말할 때.
    - 우울감이나 무료함을 호소하여, 행동적인 변화(Behavioral Activation)가 필요할 때.

    Args:
        user_emotion (str): 사용자의 현재 감정 상태 (예: "우울", "심심함", "짜증", "행복")
        mobility_status (str): 사용자의 거동 가능 여부 (기본값: "거동 가능")
    """
    print(f"[Tool: 활동 추천] 감정: {user_emotion}, 거동: {mobility_status}")

    # 0. [Pain-Aware Logic] 통증/고통이 심한 경우 (Micro-Activities)
    # 감정 키워드에 '고통', '아픔', '힘듦', '죽음', '미치겠' 등이 포함되면 DB 검색을 패스하고 즉시 처방
    pain_keywords = ["고통", "아픔", "통증", "미치겠", "죽을", "힘들", "괴로"]
    if any(k in user_emotion for k in pain_keywords) or "거동 불가" in mobility_status:
        print(">>> [Pain Mode] 통증/거동불가 감지 -> 초소형 활동(Micro-Activities) 추천")
        micro_activities = [
            "- **5-4-3-2-1 기법**: 지금 눈에 보이는 것 5개, 들리는 소리 4개, 느껴지는 감각 3개를 차례로 말해보세요. (통증 분산 효과)",
            "- **상상 여행**: 눈을 감고 가장 행복했던 여행지의 바람 냄새와 햇살을 아주 구체적으로 떠올려보세요.",
            "- **4-7-8 호흡**: 4초간 숨을 마시고, 7초간 참고, 8초간 천천히 내뱉어 보세요. 신경계를 이완시켜 줍니다.",
            "- **소리 집중**: 창밖에서 들리는 가장 작은 소리에 귀를 기울여 보세요. 새소리인가요, 바람 소리인가요?",
            "- **손가락 탭핑**: 엄지손가락으로 검지부터 새끼손가락까지 하나씩 천천히 눌러보세요."
        ]
        return "\n".join(random.sample(micro_activities, 2))

    index = pc.Index(TALK_INDEX_NAME)
    if not index: 
        return "DB 연결 오류"
    
    # 1. Logic: 감정 -> 태그 매핑
    mappings = RULES.get("mappings", {})
  
    target_tags = []
    for key, tags in mappings.get("emotion_to_feeling_tags", {}).items():
        if key in user_emotion: target_tags.extend(tags)
    if not target_tags: target_tags = ["평온/이완"]
    energy_limit = 5
    for key, val in mappings.get("mobility_to_energy_range", {}).items():
        if key in mobility_status:
            energy_limit = val.get("max_energy", 5)
            
    # 2. RAG: Pinecone Search
    query = f"효과: {', '.join(target_tags)}인 활동"
    vec = embeddings.embed_query(query)
  
    res = index.query(
        vector=vec, 
        top_k=10,
        include_metadata=True, 
        filter={"type": {"$eq": "activity"}, "ENERGY_REQUIRED": {"$lte": energy_limit}}
    )
    matches = res.get('matches', [])
    if not matches: 
        return "적절한 활동을 찾지 못했습니다."
  
    selected_matches = random.sample(matches, min(len(matches), 3))
    results = []
    for m in selected_matches:
        meta = m['metadata']
        results.append(f"- {meta.get('activity_kr')} (기대효과: {meta.get('FEELING_TAGS')})")
  
    print("[Tool] 검색 결과\n", results)
    return "\n".join(results)

@tool
def search_empathy_questions_tool(context: str) -> str:
    """
    [Tool] 사용자의 발화 맥락을 분석하여, 대화를 더 깊게 이어가고 사용자가 자신의 감정을 털어놓도록 유도하는 **'공감형 질문(Open-ended Question)'**을 검색합니다.

    [사용해야 하는 상황]
    - 사용자가 짧게 대답하거나, 대화가 끊길 것 같을 때.
    - 사용자가 슬픔, 후회, 두려움 등 무거운 감정을 표현했을 때, 섣불리 조언하기보다 경청하려 할 때.
    - 예: 사용자가 "옛날 생각이 많이 나네"라고 했을 때 -> "그 시절 중 가장 기억에 남는 장면은 무엇인가요?"와 같은 질문 확보.

    [기대 효과]
    단순한 리액션("그렇군요")을 넘어, 사용자가 자신의 인생 이야기를 회고(Life Review)하도록 돕습니다.
    """
    index = pc.Index(TALK_INDEX_NAME)
    if not index: 
        return "DB 연결 오류"
  
    vec = embeddings.embed_query(context)
    res = index.query(
        vector=vec, 
        top_k=3, 
        include_metadata=True, 
        filter={"type": {"$eq": "question"}}
    )
  
    # In-Context Learning 유도
    questions = [f"- {m['metadata'].get('question_text')} (의도: {m['metadata'].get('intent')})" for m in res['matches']]
  
    print(f"[Tool 질문]\n {questions}")
    return "\n".join(questions) if questions else "적절한 질문이 없습니다."

@tool
def search_welldying_wisdom_tool(topic: str) -> str:
    """
    [Tool] 죽음, 상실, 용서, 삶의 의미 등 철학적이고 실존적인 주제에 대해 인류의 지혜(명언, 철학서, 심리학적 통찰 등)를 검색합니다.

    [사용해야 하는 상황]
    - 사용자가 삶의 유한함, 죽음에 대한 두려움, 인생의 허무함 등을 진지하게 토로할 때.
    - 웹 검색(Fact)으로는 답을 줄 수 없는 정서적/영적 질문을 받았을 때.
    - 예: "죽으면 끝일까?", "가족에게 짐이 되기 싫어", "용서하지 못한 사람이 있어"

    [기대 효과]
    사용자에게 깊이 있는 통찰과 위로를 제공하여, 죽음 불안을 완화하고 삶의 의미를 재구성하도록 돕습니다.
    
    Args:
        topic (str): 검색할 주제 키워드 (예: "죽음의 의미", "후회 없는 삶", "용서")
    """
    index = pc.Index(WISDOM_INDEX_NAME)
    if not index: 
        return "지혜 DB 연결 오류"
  
    logger.info(f"지식 검색 요청: {topic}")
  
    vec = embeddings.embed_query(topic)
  
    # DB에 type='wisdom'으로 데이터를 적재해두었다고 가정
    res = index.query(
        vector=vec, 
        top_k=3, 
        include_metadata=True, 
        filter={"type": {"$eq": "wisdom"}}
    )
  
    matches = res.get('matches', [])
    if not matches:
        return "관련된 명언을 찾지 못했습니다. 보편적인 인류의 지혜로 답변해주세요."
  
    results = []
    for m in matches:
        meta = m['metadata']
        # content: 본문, source: 출처
        results.append(f"내용: {meta.get('content', '')}\n출처: {meta.get('source', 'Unknown')}")
  
    print("[Tool 지식 검색]", results)
    return "\n---\n".join(results)
    
# 외부 모듈에서 import 할 수 있도록 TOOLS 리스트 정의
TOOLS_TALK = [recommend_activities_tool, search_empathy_questions_tool, search_welldying_wisdom_tool, search_from_web_tool]

# Tavily 검색이 유효할 때만 추가
if tavily_search:
    TOOLS_TALK.append(tavily_search)