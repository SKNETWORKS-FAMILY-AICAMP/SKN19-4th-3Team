# Lifeclover UI - 프롬프트 버전 관리 가이드

> RAG+LLM 기반 감성 대화 챗봇 + 다이어리 서비스

---

## 📋 목차
1. [프로젝트 구조](#-프로젝트-구조)
2. [환경 설정](#-환경-설정)
3. [서버 실행](#-서버-실행)
4. [프롬프트 버전 관리](#-프롬프트-버전-관리)
5. [새 버전 추가 방법](#-새-버전-추가-방법)
6. [개발 가이드](#-개발-가이드)

---

## 📁 프로젝트 구조

```
Lifeclover-ui/
├── chatbot/
│   ├── conversation_engine.py        # LangGraph 기반 대화 엔진
│   └── chatbot_modules/
│       ├── empathy_agent.py          # 버전 선택 (v1/v2/v3/...)
│       ├── info_agent.py             # 정보 제공 에이전트
│       ├── llm_client.py             # OpenAI LLM 클라이언트
│       ├── recommend_ba.py           # Pinecone/Tavily 도구
│       ├── diary_manager.py          # 다이어리 관리
│       └── chatbot_prompts/
│           └── empathy/
│               ├── __init__.py
│               ├── v1.py             # 프롬프트 v1 + 로직
│               ├── v2.py             # 프롬프트 v2 + 로직
│               └── v3.py             # 프롬프트 v3 + 로직
├── config/
│   └── settings.py                   # Django 설정 (환경변수 로드)
├── web/
│   └── views.py                      # API 엔드포인트
├── templates/
│   └── index.html                    # 프론트엔드
├── static/
│   ├── css/
│   └── js/
├── requirements.txt                  # Python 패키지 의존성
└── manage.py                         # Django 관리 스크립트
```

---

## ⚙️ 환경 설정

### 1. 저장소 클론
```bash
git clone https://github.com/SKN-19-3rd-4th-Project/Lifeclover-ui.git
cd Lifeclover-ui
```

### 2. 브랜치 체크아웃
```bash
git checkout feat/django-ui-ksu
```

### 3. Conda 가상환경 생성 및 활성화
```bash
conda create -n ml_env python=3.12
conda activate ml_env
```

### 4. 패키지 설치
```bash
pip install -r requirements.txt
```

### 5. 환경 변수 설정
프로젝트 **상위 폴더**에 `.env` 파일 생성:

**위치**: `F:\SKN-19\.env` (또는 적절한 상위 경로)

```env
OPENAI_API_KEY=sk-proj-...
PINECONE_API_KEY=pcsk_...
TAVILY_API_KEY=tvly-...
```

> ⚠️ `.env` 파일은 절대 Git에 커밋하지 마세요!

### 6. 마이그레이션 (선택)
```bash
python manage.py migrate
```

---

## 🚀 서버 실행

```bash
python manage.py runserver
```

**접속**: http://127.0.0.1:8000/

---

## 🎯 프롬프트 버전 관리

### 현재 버전 목록

| 버전 | 특징 | 스케일 | Deep Mode | 주요 기능 |
|------|------|--------|-----------|-----------|
| **v1** | 원본 (한국어) | 0~1 | ≥ 0.6 | 기본 감성 대화 |
| **v2** | 유머 감지 개선 | 0~10 | ≥ 6 | Light Mode, 이모지 규칙 |
| **v3** | 웰라이프 코치 | 0~10 | ≥ 6 | 생활 제안, 루틴 개선 |

### 버전 전환 방법

`chatbot/chatbot_modules/empathy_agent.py` 파일 수정:

```python
PROMPT_VERSION = "v2"  # "v1", "v2", "v3" 중 선택
```

→ **서버 재시작 필수!**

---

## ➕ 새 버전 추가 방법

### Step 1: 기존 버전 복사
```bash
cd chatbot/chatbot_modules/chatbot_prompts/empathy
cp v2.py v4.py
```

### Step 2: v4.py 파일 수정
```python
# empathy/v4.py

# 프롬프트 수정
SYSTEM_PROMPT_TEMPLATE = """
You are "Lify", a warm emotional companion...

[여기에 새로운 규칙 작성]
"""

# 로직 설정 (필요시)
ALPHA = 0.7
DEEP_MODE_THRESHOLD = 6
WISDOM_INSTRUCTION_LANG = "ko"
# ...
```

### Step 3: empathy_agent.py에 버전 추가
```python
# chatbot/chatbot_modules/empathy_agent.py

PROMPT_VERSION = "v4"  # 새 버전 선택

# ...

elif PROMPT_VERSION == "v4":
    from chatbot_modules.chatbot_prompts.empathy.v4 import empathy_node
```

### Step 4: 테스트
```bash
python manage.py runserver
# 브라우저에서 테스트
```

### Step 5: 커밋 & 푸시
```bash
git add .
git commit -m "feat: 프롬프트 v4 추가 - [설명]"
git push origin feat/django-ui-ksu
```

---

## 💡 개발 가이드

### 프롬프트 작성 팁

1. **Light Mode (0~2점)**: 유머, 가벼운 대화
   - 과도한 공감 X
   - 품위 있는 반응: "재치 있으시네요", "센스 있는 표현이에요"

2. **Normal Mode (3~5점)**: 일상 고민
   - 공감 + 실용적 조언

3. **Deep Mode (6~10점)**: 깊은 고민, 실존적 질문
   - `recommend_welldying_wisdom` 도구 사용
   - 깊이 있는 위로

### 이모지 사용 규칙 (v2, v3)
- **기본**: 이모지 사용 금지
- **허용**: Light Mode + 유저가 웃음 사용 시 (ㅋㅋ, ㅎㅎ, 😂)
  - 최대 1개 (🙂 또는 😊)
- **금지**: Deep Mode에서는 절대 사용 금지

### 설정 파라미터

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `ALPHA` | 점수 업데이트 가중치 (0~1) | 0.7 |
| `NORMALIZE_INPUT` | 입력 점수 정규화 (0~1) | False |
| `DEEP_MODE_THRESHOLD` | Deep Mode 기준점 | 6 (0~10 스케일) |
| `ANALYZER_INPUT_FORMAT` | 분석기 입력 형식 | `"User message: {message}"` |
| `WISDOM_INSTRUCTION_LANG` | 위로 지혜 언어 | `"ko"` 또는 `"en"` |

---

## 🐛 트러블슈팅

### 1. `ModuleNotFoundError: No module named 'langchain'`
```bash
pip install -r requirements.txt
```

### 2. `PINECONE_API_KEY` 오류
- `.env` 파일 위치 확인 (프로젝트 상위 폴더)
- `config/settings.py`의 `env_path` 확인

### 3. `Invalid HTTP_HOST header`
- `config/settings.py`: `ALLOWED_HOSTS = ['*']` 확인

### 4. 프롬프트 변경이 반영 안 됨
- 서버 재시작 필수!
- `empathy_agent.py`의 `PROMPT_VERSION` 확인

---

## 📚 참고 문서

- **프로젝트 분석**: `PROJECT_ANALYSIS.md`
- **TODO 리스트**: `TODO_LIST.md`
- **작업 로그**: `WORK_LOG_2025-12-05.md`

---

## 👥 팀원 협업 가이드

### 브랜치 전략
- `main`: 안정화 버전
- `feat/django-ui-bsj`: 기준 브랜치
- `feat/django-ui-ksu`: 개발 브랜치
- `feat/django-ui-[이름]`: 각자 브랜치

### Pull Request 전
1. 최신 코드 pull
2. 충돌 해결
3. 테스트 완료 확인
4. 커밋 메시지 명확히

### 커밋 메시지 규칙
```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
refactor: 코드 리팩토링
test: 테스트 추가
```

**Last Updated**: 2025.12.05 

