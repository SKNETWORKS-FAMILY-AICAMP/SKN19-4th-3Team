# Lifeclover 프로젝트 작업 목록

## 🎯 목표
- 기능 + UI 연결 완성
- 두 개의 챗봇 프롬프팅 수정
- 서비스 품질 향상

---

## 📋 작업 목록

### 🔴 긴급 작업 (우선순위 높음)

#### 1. Info Agent 구현
**위치**: `chatbot/chatbot_modules/info_agent.py`
- [ ] 정보 제공 로직 구현
- [ ] 장례 시설 정보 검색 도구 추가
- [ ] 지원 정책 정보 검색 도구 추가
- [ ] 유산 상속 정보 제공 로직
- [ ] 디지털 개인정보 처리 안내 로직
- [ ] RAG 검색 연동 (`data/facilities_region_list.json`, `data/ordinance_region_list.json` 활용)

**예상 시간**: 4-6시간

---

#### 2. 프롬프트 수정 (Empathy Agent)
**위치**: `chatbot/chatbot_modules/empathy_agent.py`
- [ ] `SYSTEM_PROMPT_TEMPLATE` 개선
  - 반복적인 표현 제거
  - 더 자연스러운 공감 표현 추가
  - 예시 대화 패턴 보완
- [ ] `ACTIVITY_SYSTEM_PROMPT` 개선
- [ ] `CHOICE_SYSTEM_PROMPT` 개선
- [ ] `SEARCH_GUIDELINE_PROMPT` 개선
- [ ] `SERIOUSNESS_ANALYZER_PROMPT` 개선

**예상 시간**: 2-3시간

---

#### 3. 프롬프트 수정 (Info Agent)
**위치**: `chatbot/chatbot_modules/info_agent.py`
- [ ] `INFO_MODE_PROMPT` 상세화
- [ ] 정보 제공 톤 설정
- [ ] 출처 명시 규칙 추가
- [ ] 단계별 안내 프롬프트 작성

**예상 시간**: 1-2시간

---

#### 4. 하드코딩된 사용자 ID 제거
**위치**: `web/views.py` (50줄)
- [ ] 사용자 인증 시스템 설계
- [ ] Django User 모델 활용 또는 커스텀 모델 생성
- [ ] 세션 기반 사용자 식별 구현
- [ ] 모든 API 엔드포인트에 사용자 인증 적용

**예상 시간**: 3-4시간

---

### 🟡 중요 작업 (우선순위 중간)

#### 5. 다이어리 생성 UI 연동
**위치**: `static/js/app.js`, `web/views.py`
- [ ] 다이어리 생성 버튼 추가 (챗봇 화면)
- [ ] API 엔드포인트 확인 (`/api/diary/generate/`)
- [ ] 생성 완료 후 다이어리 페이지로 이동
- [ ] 로딩 상태 표시

**예상 시간**: 1-2시간

---

#### 6. 에러 핸들링 강화
**위치**: 전역
- [ ] LLM API 실패 시 fallback 메시지
- [ ] Pinecone 연결 실패 처리
- [ ] 네트워크 오류 처리
- [ ] 사용자 친화적 에러 메시지

**예상 시간**: 2-3시간

---

#### 7. 세션 관리 개선
**위치**: `chatbot/chatbot_modules/session_manager.py`
- [ ] 동시성 문제 해결 (파일 락)
- [ ] 세션 만료 처리
- [ ] 대화 히스토리 정리 (오래된 기록 삭제)

**예상 시간**: 2-3시간

---

#### 8. UI/UX 개선
**위치**: `static/js/app.js`, `templates/index.html`, `static/css/style.css`
- [ ] 로딩 애니메이션 개선
- [ ] 메시지 전송 피드백 강화
- [ ] 반응형 디자인 보완
- [ ] 접근성 개선 (ARIA 라벨 등)
- [ ] 다이어리 캘린더 UI 개선

**예상 시간**: 4-6시간

---

### 🟢 개선 작업 (우선순위 낮음)

#### 9. 사용자 프로필 시스템
**위치**: `web/models.py`, `templates/`, `static/js/app.js`
- [ ] 사용자 프로필 모델 생성
- [ ] 초기 설정 화면 추가
- [ ] 프로필 수정 기능

**예상 시간**: 3-4시간

---

#### 10. 다이어리 기능 강화
**위치**: `chatbot/chatbot_modules/diary_manager.py`, `web/views.py`
- [ ] 다이어리 수정 기능
- [ ] 다이어리 삭제 기능 (UI 연동)
- [ ] 감정 추이 그래프

**예상 시간**: 3-4시간

---

#### 11. 대화 품질 개선
**위치**: `chatbot/conversation_engine.py`
- [ ] 대화 히스토리 요약 (토큰 절약)
- [ ] 컨텍스트 윈도우 관리
- [ ] 중복 응답 방지 로직

**예상 시간**: 2-3시간

---

#### 12. 성능 최적화
**위치**: 전역
- [ ] API 응답 시간 측정
- [ ] 캐싱 시스템 도입 (Redis)
- [ ] 비동기 처리 (Celery)

**예상 시간**: 4-6시간

---

## 📝 작업 진행 방법

### 1단계: 긴급 작업 완료
1. Info Agent 구현 (가장 중요)
2. 프롬프트 수정 (두 에이전트)
3. 사용자 ID 하드코딩 제거

### 2단계: 기능 연결
1. 다이어리 생성 UI 연동
2. 에러 핸들링 강화
3. UI/UX 개선

### 3단계: 품질 향상
1. 세션 관리 개선
2. 대화 품질 개선
3. 성능 최적화

---

## 🔍 각 작업별 상세 가이드

### Info Agent 구현 가이드

**필요한 도구**:
1. 장례 시설 검색 도구
2. 지원 정책 검색 도구
3. 유산 상속 정보 도구
4. 디지털 정보 처리 도구

**데이터 소스**:
- `data/facilities_region_list.json`
- `data/ordinance_region_list.json`
- `data/users.json` (참고용)

**구현 예시**:
```python
@tool
def search_funeral_facilities_tool(region: str, facility_type: str) -> str:
    """장례 시설 정보 검색"""
    # JSON 파일에서 검색 또는 Pinecone RAG 활용
    pass
```

---

### 프롬프트 수정 가이드

**Empathy Agent 프롬프트 개선 포인트**:
1. 반복 표현 제거 ("~라고 느끼고 계시는군요" 등)
2. 더 자연스러운 공감 표현
3. 예시 대화 패턴 다양화
4. 활동 제안 톤 개선

**Info Agent 프롬프트 작성 포인트**:
1. 사실 기반 답변 강조
2. 출처 명시 규칙
3. 단계별 안내 구조
4. 감정적 표현 최소화

---

## 📊 진행 상황 추적

- [ ] 긴급 작업 완료
- [ ] 중요 작업 완료
- [ ] 개선 작업 완료

**마지막 업데이트**: 2025-01-XX

---

## 💡 추가 아이디어

### 단기 아이디어
- 대화 내보내기 기능 (PDF, 텍스트)
- 다이어리 공유 기능 (가족에게)
- 감정 일기 기능

### 장기 아이디어
- 음성 입력 지원
- 다국어 지원
- 모바일 앱 개발

---

**작성일**: 2025-01-XX  
**작성자**: AI Assistant

