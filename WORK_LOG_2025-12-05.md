# 작업 내역 (2025.12.05)

작업자: ksu  
브랜치: `feat/django-ui-ksu`  
기준 브랜치: `feat/django-ui-bsj`

---

## 1. Git 작업 및 프로젝트 환경 설정

### Git 브랜치 작업
- ✅ `feat/django-ui-bsj` 브랜치를 클론
- ✅ `feat/django-ui-ksu` 브랜치 생성 및 체크아웃
- ✅ `test.txt` 파일로 push 테스트 완료
- ✅ Git 사용자 정보 설정 (user.name, user.email)


## 2. 환경 변수 설정 개선

### `.env` 파일 경로를 프로젝트 밖으로 수정 (혹시모를 업로드 방지)
- **`.env` 위치**: `F:\SKN-19\.env`
- **`config/settings.py` 수정**:
  ```python
  from pathlib import Path
  from dotenv import load_dotenv

  BASE_DIR = Path(__file__).resolve().parent.parent
  env_path = BASE_DIR.parent.parent / '.env'
  load_dotenv(dotenv_path=env_path)
  ```

### 중복 코드 제거 (환경 변수 로드 중앙화)
- **`chatbot_modules/llm_client.py`**: `load_dotenv()` 제거
- **`chatbot_modules/recommend_ba.py`**: 
  - `load_dotenv()` 제거
  - `PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")` 주석 해제

**개선 효과**: 
- 환경 변수를 Django `settings.py`에서 중앙 관리
- 중복 코드 제거로 유지보수성 향상

### Django 설정
- **`config/settings.py`**: `ALLOWED_HOSTS = ['*']  # 모든 호스트 허용 (개발용)`
- 서버 접근 권한 문제 해결

---

## 3. 패키지 의존성 해결

### 설치한 패키지 (`requirements.txt`)
```txt
Django>=5.0,<6.0
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.1.0
langgraph>=0.1.0
langchain-tavily>=0.1.0
pinecone-client==3.0.0
python-dotenv>=1.0.0
openai>=1.0.0
```

### 해결한 오류
1. **`ModuleNotFoundError: No module named 'langchain_tavily'`**
   - 해결: `pip install langchain-tavily`

2. **Pinecone 버전 충돌**
   - 문제: `pinecone==6.0.0`과 `pinecone-client` 충돌
   - 해결: `pinecone-client==3.0.0` 사용 (코드베이스와 호환)

3. **`TAVILY_API_KEY` 로드 오류**
   - 문제: `.env` 파일 경로 불일치
   - 해결: `settings.py`의 `env_path` 수정

4. **`Invalid HTTP_HOST header`**
   - 문제: Django `ALLOWED_HOSTS` 미설정
   - 해결: `['127.0.0.1', 'localhost']` 추가

---

## 4. 프롬프트 버전 관리 시스템 구축 ⭐

### 기존 문제점
- 프롬프트를 수정할 때마다 원본 파일을 덮어써야 함
- 여러 버전을 테스트하기 어려움
- 이전 버전으로 롤백이 어려움

### 새로운 구조
```
chatbot_modules/
├── empathy_agent.py          # 버전 선택 (v1/v2/v3 중 선택)
└── chatbot_prompts/
    └── empathy/
        ├── __init__.py       # Python 패키지 선언
        ├── v1.py             # 프롬프트 v1 + 로직
        ├── v2.py             # 프롬프트 v2 + 로직
        └── v3.py             # 프롬프트 v3 + 로직
```

### `empathy_agent.py` 구조
```python
# 역할: v1 / v2 / v3 중에서 선택해서 불러오기

# 버전 선택 (이 한 줄만 바꾸면 됨!)
PROMPT_VERSION = "v2"  # "v1", "v2", "v3" 중에서 선택

# 버전별 import
if PROMPT_VERSION == "v1":
    from chatbot_modules.chatbot_prompts.empathy.v1 import empathy_node
elif PROMPT_VERSION == "v2":
    from chatbot_modules.chatbot_prompts.empathy.v2 import empathy_node
elif PROMPT_VERSION == "v3":
    from chatbot_modules.chatbot_prompts.empathy.v3 import empathy_node
else:
    raise ValueError(f"Unknown PROMPT_VERSION: {PROMPT_VERSION}")

__all__ = ["empathy_node"]
```

### 버전별 특징

#### v1 (원본)
- **프롬프트 언어**: 한국어
- **점수 스케일**: 0~1
- **Deep Mode 기준**: >= 0.6
- **설정**:
  - `ALPHA = 0.7`
  - `NORMALIZE_INPUT = True`
  - `ANALYZER_INPUT_FORMAT = "사용자 발화: {message}"`
  - `WISDOM_INSTRUCTION_LANG = "ko"`

#### v2 (유머 감지 개선)
- **프롬프트 언어**: 영어 + 한국어 혼합
- **점수 스케일**: 0~10
- **Deep Mode 기준**: >= 6
- **새로운 기능**:
  - Light Mode (≤ 2점): 유머 감지 및 품위 있는 반응
  - 이모지 규칙: Light Mode + 유저 웃음 사용 시에만 허용
  - 유저 웃음 감지 (`user_used_laughter`)
- **설정**:
  - `ALPHA = 0.7`
  - `NORMALIZE_INPUT = False`
  - `ANALYZER_INPUT_FORMAT = "User message: {message}"`
  - `WISDOM_INSTRUCTION_LANG = "en"`
  - `INCLUDE_RUNTIME_INSTRUCTION = True`

#### v3 (웰라이프 코치)
- **프롬프트 언어**: 영어 + 한국어
- **점수 스케일**: 0~10
- **Deep Mode 기준**: >= 6
- **특징**:
  - 감정 공감 + 생활 개선 제안 (welllife 코치)
  - 일상 루틴, 건강, 사회적 연결 제안
  - 유머 감지 및 품위 있는 반응
- **설정**:
  - `ALPHA = 0.7`
  - `NORMALIZE_INPUT = False`
  - `ANALYZER_INPUT_FORMAT = "User message: {message}"`
  - `WISDOM_INSTRUCTION_LANG = "ko"`
  - `INCLUDE_RUNTIME_INSTRUCTION = True`

### 버전 변경 방법
1. `empathy_agent.py` 열기
2. `PROMPT_VERSION = "v2"` → `"v1"` 또는 `"v3"`로 변경
3. 서버 재시작 (`python manage.py runserver`)

### 장점
- ✅ 버전 간 완전 독립 (프롬프트 + 로직 모두 분리)
- ✅ 한 줄만 바꾸면 버전 전환
- ✅ 이전 버전 보존 (롤백 용이)
- ✅ 여러 버전 병렬 테스트 가능

---

## 5. v2 프롬프트 개선 (유머 감지)

### 배경
- 사용자가 아재개그를 했는데 너무 진지하게 받아서 대화 의욕 저하
- "재치 있는 표현" 인정 필요

### 추가된 기능

#### 1. Light Mode (≤ 2점)
```
- "재치 있으시네요, 살짝 웃음이 나네요."
- "센스 있는 표현이세요, 듣고 있으니 기분이 조금 가벼워지네요."
- "말씀을 이렇게 풀어주시니까 분위기가 한결 부드러워지네요."
```

#### 2. 이모지 규칙
- **기본**: 이모지 사용 금지
- **허용 조건**: 
  - `seriousness_score ≤ 2` AND
  - 유저가 웃음 표현 사용 (ㅋㅋ, ㅎㅎ, 하하, 😂, 🤣)
- **허용 이모지**: 🙂 또는 😊 (최대 1개)
- **금지**: Deep Mode (≥ 6점)에서는 절대 사용 금지

#### 3. 유저 웃음 감지
- `user_used_laughter = true/false`
- 감지 대상: "ㅋㅋ", "ㅎㅎ", "하하", 😂, 🤣 등

#### 4. 과도한 공감 방지
- Light Mode에서는 무거운 공감 멘트 자제
- "존재 자체가 소중하다" 같은 표현 제외

---

## 6. 파일 정리

### 생성된 파일
- ✅ `chatbot_modules/chatbot_prompts/empathy/__init__.py`
- ✅ `chatbot_modules/chatbot_prompts/empathy/v1.py`
- ✅ `chatbot_modules/chatbot_prompts/empathy/v2.py`
- ✅ `chatbot_modules/chatbot_prompts/empathy/v3.py`

### 수정된 파일
- ✅ `config/settings.py` - 환경변수 중앙 로드
- ✅ `chatbot_modules/llm_client.py` - 중복 코드 제거
- ✅ `chatbot_modules/recommend_ba.py` - 중복 코드 제거, API key 주석 해제
- ✅ `chatbot_modules/empathy_agent.py` - 버전 선택 로직으로 전환
- ✅ `requirements.txt` - 의존성 추가

### 삭제된 파일
- ❌ `chatbot_modules/prompt_registry.py` (불필요한 중간 레이어)

---

## 7. 서버 실행 성공 ✅

```bash
python manage.py runserver
```

**결과**:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### 남은 경고
```
You have 18 unapplied migration(s).
Your project may not work properly until you apply the migrations for app(s): 
admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.
```
→ 추후 마이그레이션 실행 예정

---

## 8. 시도했다가 되돌린 작업

### UI 프롬프트 선택기
- **시도**: `index.html`에 `<select>` 추가하여 v1/v2/v3 선택
- **문제**: Python import는 서버 시작 시 1회만 실행됨
- **결과**: 동적 변경 불가능 → **되돌림**
- **결론**: `empathy_agent.py`에서 직접 선택하는 방식이 더 정확함

---

## 요약

### 핵심 성과 🎯
1. ✅ **프로젝트 환경 구성 완료** (Git, Conda, 패키지)
2. ✅ **서버 정상 실행** (http://127.0.0.1:8000/)
3. ✅ **프롬프트 버전 관리 시스템 구축** (v1/v2/v3)
4. ✅ **v2 프롬프트 유머 감지 개선**
5. ✅ **환경 변수 로드 중앙화** (중복 코드 제거)

### 다음 작업 (TODO) 📋
- [ ] `python manage.py migrate` 실행
- [ ] 프롬프트 v1/v2/v3 실제 테스트
- [ ] Info Agent 구현 및 프롬프트 작성
- [ ] 사용자 ID 하드코딩 제거
- [ ] 다이어리 생성 UI 연동
- [ ] UI/UX 개선 (로딩 애니메이션, 반응형)

### 커밋 대기 중 💾
- 환경 설정 개선
- 프롬프트 버전 관리 시스템
- 중복 코드 제거
- v2, v3 프롬프트 추가

---

## 작업 시간
- 시작: 오후 (정확한 시간 미기록)
- 종료: 저녁 (정확한 시간 미기록)
- 주요 난관: 패키지 의존성, 환경 변수 경로, Git 브랜치 이해

## 참고
- 프로젝트: Lifeclover (RAG+LLM 챗봇+다이어리 서비스)
- 목표: UI와 기능 연결, 프롬프트 개선, 서비스 품질 향상

