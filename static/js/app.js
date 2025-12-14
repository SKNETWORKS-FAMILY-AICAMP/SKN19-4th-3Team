if (window.__LIFECLOVER_APP_INIT__) {
  // already initialized; prevent double binding
} else {
  window.__LIFECLOVER_APP_INIT__ = true;

  document.addEventListener('DOMContentLoaded', () => {
    const state = {
      currentPage: 'home',
      isLoggedIn: false,
      userName: '회원',
      userProfile: null, // User profile data from login
      preferredName: null, // User's preferred name
      mobilityStatus: null, // User's mobility status
      emotionStatus: null, // User's emotional state
      messagesChat: [],
      messagesInfo: [],
      currentMode: 'chat', // 'chat' or 'info'
      selectedServiceType: null, // For info mode context
      isLoading: false
    };

    // Will be loaded from backend
    let diaryEntries = {};

    const sections = document.querySelectorAll('.page-section');
    const pageTriggers = document.querySelectorAll('[data-target-page]');
    const navElement = document.querySelector('.nav');
    const navIndicator = document.querySelector('.nav-indicator');
    const authContainer = document.querySelector('[data-auth]');
    const loginModal = document.querySelector('[data-login-modal]');
    const loginForm = document.querySelector('[data-login-form]');
    const loginCloseBtn = document.querySelector('[data-login-close]');
    const loginCancelBtn = document.querySelector('[data-login-cancel]');
    const deleteModal = document.querySelector('[data-delete-modal]');
    const deleteText = document.querySelector('[data-delete-text]');
    const deleteCloseBtn = document.querySelector('[data-delete-close]');
    const deleteCancelBtn = document.querySelector('[data-delete-cancel]');
    const deleteConfirmBtn = document.querySelector('[data-delete-confirm]');
    const servicesGrid = document.querySelector('[data-services-grid]');
    const chatPanels = document.querySelectorAll('[data-chat-panel]');
    const chatInputs = document.querySelectorAll('[data-chat-input]');
    const sendButtons = document.querySelectorAll('[data-send-message]');
    const quickToggle = document.querySelector('[data-quick-toggle]');
    const quickPanel = document.querySelector('[data-quick-panel]');
    const quickItems = document.querySelectorAll('[data-quick-question]');
    const askQuestionChip = document.querySelector('.ask-question-chip');
    const askSwiperEl = document.querySelector('.ask-swiper');
    const textAreas = document.querySelectorAll('.chat-input');
    const generateDiaryBtn = document.querySelector('[data-generate-diary]');
    const bodyEl = document.body;
    let navIndicatorReady = false;
    const monthTitleEl = document.querySelector('[data-month-title]');
    const calendarGridEl = document.querySelector('[data-calendar-grid]');
    const diaryDetailEl = document.querySelector('[data-diary-detail]');
    const monthButtons = document.querySelectorAll('[data-change-month]');
    const signupForm = document.querySelector('[data-signup-form]');
    const checklistContainer = document.querySelector('[data-checklist]');
    const progressText = document.querySelector('[data-progress-text]');
    const progressBar = document.querySelector('[data-progress-bar]');

    const formatDateKey = (date) => {
      const y = date.getFullYear();
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const d = String(date.getDate()).padStart(2, '0');
      return `${y}-${m}-${d}`;
    };

    let currentMonth = new Date();
    let selectedDateKey = formatDateKey(new Date());
    let checklistLoaded = false;
    const checklistData = [];
    let checklistTotal = 0;

    function switchPage(page) {
      if (!page) return;
      state.currentPage = page;
      state.currentMode = page === 'services' ? 'info' : 'chat';

      sections.forEach((section) => {
        const isActive = section.dataset.page === page;
        section.classList.toggle('active', isActive);
        section.hidden = !isActive;
      });

      pageTriggers.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.targetPage === page);
      });

      if (page === 'services') {
        // 처음 진입하거나 대화 기록이 없으면 카드 다시 노출
        if (servicesGrid && state.messagesInfo.length === 0) {
          servicesGrid.classList.remove('is-hidden');
        }
      }

      moveNavIndicator();

      // Load diaries when switching to diary page
      if (page === 'diary') {
        // 바로 달력 렌더링해 비어 있어도 구조가 보이도록
        renderCalendar();
        loadDiaries();
        selectedDateKey = formatDateKey(currentMonth);
        renderDiaryDetail();
      }

      if (page === 'chat' && state.messagesChat.length === 0) {
        initializeChat();
      }
      if (page === 'services') {
        renderMessages();
      }
      if (page === 'signup') {
        loadChecklist();
        updateProgress();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });

      // Body 스크롤 제어: 대화/정보 탭에서는 전역 스크롤 숨김
      if (bodyEl) {
        if (state.currentPage === 'chat' || state.currentPage === 'services') {
          bodyEl.classList.add('chat-mode');
        } else {
          bodyEl.classList.remove('chat-mode');
        }
      }
    }

    pageTriggers.forEach((btn) => {
      btn.addEventListener('click', () => switchPage(btn.dataset.targetPage));
    });

    function autoResizeTextarea(el) {
      if (!el) return;
      el.style.height = 'auto';
      const maxHeight = 240;
      const newHeight = Math.min(el.scrollHeight, maxHeight);
      el.style.height = `${newHeight}px`;
      el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden';
    }

    textAreas.forEach((ta) => {
      autoResizeTextarea(ta);
      ta.addEventListener('input', () => autoResizeTextarea(ta));
    });

    function initAskSwiper() {
      if (!askSwiperEl || !window.Swiper) return;

      const swiper = new Swiper(askSwiperEl, {
        spaceBetween: 30,
        centeredSlides: true,
        loop: true,
        autoplay: {
          delay: 3500,
          disableOnInteraction: false,
        },
        pagination: {
          el: '.ask-dots',
          clickable: true,
        },
        navigation: {
          nextEl: '.ask-stage .swiper-button-next',
          prevEl: '.ask-stage .swiper-button-prev',
        },
        on: {
          init: function () {
            updateChip(this.realIndex);
          },
          slideChange: function () {
            updateChip(this.realIndex);
          }
        }
      });

      function updateChip(idx) {
        if (!askQuestionChip) return;
        const slides = askSwiperEl.querySelectorAll('.ask-slide');
        const target = slides[idx % slides.length];
        const text = target?.dataset?.question || '라잎이에게 궁금한 것을 물어보세요';
        askQuestionChip.textContent = text;
      }

      return swiper;
    }

    function moveNavIndicator() {
      if (!navIndicator || !navElement) return;
      const activeBtn = navElement.querySelector(`.nav-item[data-target-page="${state.currentPage}"]`);
      if (!activeBtn || state.currentPage === 'home') {
        navIndicator.style.opacity = '0';
        navIndicatorReady = false; // 홈에서는 위치 유지, 준비 플래그 해제
        return;
      }

      const navRect = navElement.getBoundingClientRect();
      const btnRect = activeBtn.getBoundingClientRect();
      const centerX = btnRect.left - navRect.left + btnRect.width / 2;
      const indicatorWidth = btnRect.width + 16;
      const indicatorHeight = btnRect.height + 10;

      navIndicator.style.width = `${indicatorWidth}px`;
      navIndicator.style.height = `${indicatorHeight}px`;
      navIndicator.style.transform = `translate(${centerX - indicatorWidth / 2}px, -50%)`;
      navIndicator.style.opacity = '1';

      // 첫 표시 후에만 슬라이드 애니메이션 활성화
      if (!navIndicatorReady) {
        navIndicatorReady = true;
        requestAnimationFrame(() => navIndicator.classList.add('ready'));
      }
    }

    // Service card click handlers
    const defaultCardQuestions = {
      funeral_facilities: '장례 시설 정보를 알려주세요.',
      support_policy: '장례 지원 정책이 궁금합니다.',
      inheritance: '유산 상속 절차를 알려주세요.',
      digital_info: '디지털 정보 처리 방법을 알려주세요.'
    };

    document.querySelectorAll('.service-card').forEach((card) => {
      card.addEventListener('click', () => {
        const title = card.querySelector('.service-title')?.textContent || '';

        // Map service titles to internal types
        const serviceTypeMap = {
          '장례 시설 안내': 'funeral_facilities',
          '지원 정책': 'support_policy',
          '유산 상속 안내': 'inheritance',
          '디지털 개인 정보': 'digital_info'
        };

        state.selectedServiceType = serviceTypeMap[title] || null;
        state.currentMode = 'info';
        servicesGrid?.classList.add('is-hidden');

        const question = defaultCardQuestions[state.selectedServiceType] || `${title} 정보를 알려주세요.`;
        // Clear messages and send default question
        if (state.messagesInfo.length === 0) state.messagesInfo = [];
        renderMessages();
        switchPage('services');
        sendMessage('services', question);
      });
    });

    function renderAuth() {
      if (!authContainer) return;
      authContainer.innerHTML = '';

      if (state.isLoggedIn) {
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'button button-signup';
        deleteBtn.textContent = '회원 탈퇴';
        deleteBtn.addEventListener('click', () => openDeleteModal());

        const logoutBtn = document.createElement('button');
        logoutBtn.className = 'button button-logout';
        logoutBtn.textContent = '로그아웃';
        logoutBtn.addEventListener('click', () => {
          state.isLoggedIn = false;
          state.userName = '회원';
          state.userProfile = null;
          state.preferredName = null;
          state.mobilityStatus = null;
          state.emotionStatus = null;
          state.messagesChat = [];
          renderAuth();
        });
        authContainer.appendChild(deleteBtn);
        authContainer.appendChild(logoutBtn);
        return;
      }

      const loginBtn = document.createElement('button');
      loginBtn.type = 'button';
      loginBtn.className = 'button button-login';
      loginBtn.textContent = '로그인';
      loginBtn.addEventListener('click', () => {
        openLoginModal();
      });

      const signupBtn = document.createElement('button');
      signupBtn.type = 'button';
      signupBtn.className = 'button button-signup';
      signupBtn.textContent = '회원가입';
      signupBtn.addEventListener('click', () => {
        switchPage('signup');
      });

      authContainer.appendChild(loginBtn);
      authContainer.appendChild(signupBtn);
    }

    function openLoginModal() {
      if (!loginModal) return;
      loginModal.hidden = false;
      requestAnimationFrame(() => loginModal.classList.add('is-visible'));
      const firstInput = loginModal.querySelector('input[name="username"]');
      firstInput?.focus();
    }

    function closeLoginModal() {
      if (!loginModal) return;
      loginModal.classList.remove('is-visible');
      setTimeout(() => {
        loginModal.hidden = true;
      }, 150);
    }

    loginCloseBtn?.addEventListener('click', closeLoginModal);
    loginCancelBtn?.addEventListener('click', closeLoginModal);

    loginModal?.addEventListener('click', (e) => {
      if (e.target === loginModal) closeLoginModal();
    });

    loginForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(loginForm);
      const username = (formData.get('username') || '').toString().trim();
      const password = (formData.get('password') || '').toString().trim();

      if (!username || !password) {
        alert('아이디와 비밀번호를 입력해주세요.');
        return;
      }

      try {
        const response = await fetch('/api/login/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: username,
            password: password
          })
        });

        const data = await response.json();

        if (data.success) {
          // 로그인 성공: 상태 업데이트
          state.isLoggedIn = true;
          state.userName = username;
          state.userProfile = data.profile || {};
          state.preferredName = data.profile?.preferred_name || username;
          state.mobilityStatus = data.profile?.mobility_display || '';
          state.emotionStatus = data.profile?.emotion_display || '';

          renderAuth();
          closeLoginModal();

          // 채팅 메시지 초기화 (로그인 후 환영 메시지)
          state.messagesChat = [];
          if (state.currentPage === 'chat') {
            initializeChat();
          }
        } else {
          // 로그인 실패: 경고 메시지 표시
          alert(data.message || '로그인에 실패했습니다.');
        }
      } catch (error) {
        console.error('Login error:', error);
        alert('로그인 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
    });

    function openDeleteModal() {
      if (!deleteModal) return;
      if (deleteText) deleteText.textContent = `${state.userName}님 탈퇴하시겠습니까?🥺`;
      deleteModal.hidden = false;
      requestAnimationFrame(() => deleteModal.classList.add('is-visible'));
    }

    function closeDeleteModal() {
      if (!deleteModal) return;
      deleteModal.classList.remove('is-visible');
      setTimeout(() => { deleteModal.hidden = true; }, 150);
    }

    deleteCloseBtn?.addEventListener('click', closeDeleteModal);
    deleteCancelBtn?.addEventListener('click', closeDeleteModal);
    deleteModal?.addEventListener('click', (e) => {
      if (e.target === deleteModal) closeDeleteModal();
    });
    deleteConfirmBtn?.addEventListener('click', async () => {
      try {
        // 백엔드 API로 회원탈퇴 요청
        const response = await fetch('/api/withdraw/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        const data = await response.json();

        if (data.success) {
          alert(data.message || '회원탈퇴가 완료되었습니다.');
          // 탈퇴 성공 후 로그아웃 처리
          state.isLoggedIn = false;
          state.userName = '회원';
          renderAuth();
          closeDeleteModal();
          switchPage('home');
        } else {
          alert(data.message || '회원탈퇴에 실패했습니다.');
        }
      } catch (error) {
        console.error('Withdraw error:', error);
        alert('회원탈퇴 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
    });

    function renderMessages() {
      const scrollToBottom = (el) => {
        if (!el) return;
        const last = el.lastElementChild;
        const doScroll = (behavior = 'smooth') => {
          el.scrollTo({ top: el.scrollHeight, behavior });
          if (last?.scrollIntoView) last.scrollIntoView({ behavior, block: 'end' });
        };
        // 1) 즉시
        doScroll('auto');
        // 2) 렌더 뒤 한번 더
        requestAnimationFrame(() => doScroll());
        // 3) 느린 케이스 대비 딜레이 한번 더
        setTimeout(() => doScroll(), 120);
      };

      chatPanels.forEach((panel) => {
        const key = panel.dataset.chatPanel;
        const msgEl = panel.querySelector(`[data-chat-messages="${key}"]`);
        if (!msgEl) return;

        const messages =
          key === 'services' ? state.messagesInfo :
            key === 'chat' ? state.messagesChat : [];

        msgEl.innerHTML = '';
        msgEl.classList.toggle('has-content', messages.length > 0);
        msgEl.style.display = messages.length ? 'flex' : 'none';
        panel.classList.toggle('is-chatting', messages.length > 0);

        messages.forEach((msg) => {
          const wrapper = document.createElement('div');
          wrapper.className = `message ${msg.role}`;

          const content = document.createElement('div');
          content.className = 'message-content';
          if (msg.loading) {
            content.classList.add('loading');
            content.innerHTML = `
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          `;
          } else {
          if (typeof marked !== 'undefined') {
            content.innerHTML = marked.parse(msg.content); 
            content.classList.add('markdown-body'); 
          } else {
            content.textContent = msg.content;
          }
        }

          wrapper.appendChild(content);
          msgEl.appendChild(wrapper);
        });

        scrollToBottom(msgEl);
      });
    }

    function initializeChat() {
      // Add welcome message for empathy mode
      if (state.currentMode === 'chat' && state.messagesChat.length === 0) {
        let welcomeMessage = '안녕하세요! 오늘은 좀 어떠신가요? 편하게 말씀해주세요.';

        // 로그인된 사용자의 경우 개인화된 환영 메시지
        if (state.isLoggedIn && state.preferredName) {
          const name = state.preferredName;
          welcomeMessage = `안녕하세요, ${name}님! 오늘은 좀 어떠신가요?`;

          // 거동 상태나 감정 상태가 있으면 추가 멘트
          if (state.mobilityStatus || state.emotionStatus) {
            const statusParts = [];
            if (state.mobilityStatus) statusParts.push(state.mobilityStatus);
            if (state.emotionStatus) statusParts.push(state.emotionStatus);
            welcomeMessage += ` (${statusParts.join(', ')})`;
          }

          welcomeMessage += ' 편하게 말씀해주세요.';
        }

        state.messagesChat = [
          { role: 'bot', content: welcomeMessage }
        ];
        renderMessages();
      }
    }

    const getActivePanelKey = () => (state.currentPage === 'services' ? 'services' : 'chat');

    function getPanelElements(panelKey) {
      const panel = document.querySelector(`[data-chat-panel="${panelKey}"]`);
      return {
        inputEl: panel?.querySelector(`[data-chat-input="${panelKey}"]`),
        messagesEl: panel?.querySelector(`[data-chat-messages="${panelKey}"]`),
      };
    }

    async function sendMessage(panelKey = getActivePanelKey(), presetText = null) {
      const { inputEl } = getPanelElements(panelKey);
      const text = (presetText !== null ? presetText : (inputEl?.value || '')).trim();
      if (!text || state.isLoading) return;

      console.log('[sendMessage]', panelKey, text);

      const getMessages = () => (panelKey === 'services' ? state.messagesInfo : state.messagesChat);
      const setMessages = (arr) => {
        if (panelKey === 'services') state.messagesInfo = arr;
        else state.messagesChat = arr;
      };

      let targetMessages = getMessages();

      // 1. 사용자 메시지 UI 즉시 추가
      targetMessages.push({ role: 'user', content: text });
      renderMessages();
      if (inputEl) inputEl.value = '';

      // 2. 봇 메시지 Placeholder(빈 껍데기) 추가
      // loading: true 상태로 두면 점 3개 애니메이션이 나옴.
      // 스트리밍이 시작되면 loading을 false로 바꾸고 내용을 채울 예정.
      const botMsgObj = { role: 'bot', content: '', loading: true };
      targetMessages.push(botMsgObj);
      renderMessages();

      state.isLoading = true;

      try {
        if (panelKey === 'services' && servicesGrid) {
          servicesGrid.classList.add('is-hidden');
        }

        const response = await fetch('/api/chat/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: text,
            mode: state.currentMode,
            service_type: state.selectedServiceType
          })
        });

        if (!response.ok) {
           const errData = await response.json().catch(() => ({}));
           throw new Error(errData.error || `HTTP ${response.status}`);
        }

        // [수정] 스트리밍 데이터 읽기 시작
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let isFirstChunk = true;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Uint8Array를 텍스트로 변환
          const chunk = decoder.decode(value, { stream: true });
          
          if (isFirstChunk) {
            // 첫 데이터가 들어오면 로딩 상태 해제
            botMsgObj.loading = false;
            isFirstChunk = false;
          }

          // 메시지 내용에 청크 누적
          botMsgObj.content += chunk;
          
          // UI 다시 그리기 (실시간 업데이트)
          // renderMessages 함수 안에서 marked.parse가 호출되어 마크다운이 렌더링됨
          renderMessages();
        }

        // 스트리밍 완료 후 처리
        if (panelKey === 'services') state.selectedServiceType = null;

      } catch (error) {
        // 에러 발생 시 로딩 메시지 제거 후 에러 메시지 추가
        targetMessages = targetMessages.filter(msg => msg !== botMsgObj);
        setMessages(targetMessages);
        
        targetMessages.push({
          role: 'bot',
          content: `서버와 연결할 수 없습니다. (${error.message || error}) 잠시 후 다시 시도해주세요.`
        });
        console.error('Chat error:', error);
      } finally {
        state.isLoading = false;
        renderMessages();
      }
    }

    chatInputs.forEach((input) => {
      const key = input.dataset.chatInput;
      input.addEventListener('keyup', (event) => {
        if (event.isComposing) return;
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendMessage(key);
        }
      });
    });

    sendButtons.forEach((btn) => {
      const key = btn.dataset.sendMessage;
      btn.addEventListener('click', () => sendMessage(key));
    });

    quickToggle?.addEventListener('click', () => {
      if (!quickPanel) return;
      quickPanel.classList.toggle('is-open');
    });

    const quickExamples = {
      funeral_facilities: '장례식장/화장시설 위치와 비용을 알려주세요.',
      support_policy: '지자체 장례 지원 정책이 궁금해요.',
      inheritance: '유산 상속 절차를 간단히 설명해 주세요.',
      digital_info: '사망 후 디지털 계정 처리 방법이 궁금해요.'
    };

    quickItems.forEach((item) => {
      item.addEventListener('click', () => {
        const key = item.dataset.quickQuestion;
        state.selectedServiceType = key;
        const text = quickExamples[key] || '';
        const { inputEl } = getPanelElements('services');
        if (inputEl) {
          inputEl.value = text;
          inputEl.focus();
        }
        sendMessage('services');
        quickPanel?.classList.remove('is-open');
      });
    });

    // Diary functionality
    async function loadDiaries() {
      diaryEntries = {};
      try {
        const response = await fetch('/api/diaries/');
        const data = await response.json();

        if (data.error) {
          console.error('Failed to load diaries:', data.error);
        } else if (Array.isArray(data.diaries)) {
          data.diaries.forEach(diary => {
            diaryEntries[diary.date] = {
              emoji: diary.emoji,
              tag: diary.tags,
              content: null // Will be loaded on demand
            };
          });
        }
      } catch (error) {
        console.error('Error loading diaries:', error);
      } finally {
        renderCalendar(); // 캘린더는 항상 표시
      }
    }

    async function generateDiary() {
      if (!generateDiaryBtn) return;
      generateDiaryBtn.disabled = true;
      const originalText = generateDiaryBtn.textContent;
      generateDiaryBtn.textContent = '생성 중...';
      try {
        const response = await fetch('/api/diary/generate/', { method: 'POST' });
        const data = await response.json();

        if (!response.ok || data.error) {
          const msg = data.error || data.message || '다이어리 생성 중 오류가 발생했습니다.';
          alert(msg);
          return;
        }

        await loadDiaries();
        selectedDateKey = formatDateKey(new Date());
        renderCalendar();
        renderDiaryDetail();
        alert('다이어리가 생성되었습니다.');
      } catch (error) {
        console.error('Generate diary error:', error);
        alert('다이어리 생성 중 오류가 발생했습니다.');
      } finally {
        generateDiaryBtn.textContent = originalText;
        generateDiaryBtn.disabled = false;
      }
    }

    async function loadDiaryDetail(dateKey) {
      try {
        const response = await fetch(`/api/diary/${dateKey}/`);
        const data = await response.json();

        if (data.error) {
          console.error('Failed to load diary detail:', data.error);
          return null;
        }

        return data.content;
      } catch (error) {
        console.error('Error loading diary detail:', error);
        return null;
      }
    }

    const formatMonthTitle = (date) => `${date.getFullYear()}년 ${date.getMonth() + 1}월`;

    const isSameMonth = (dateKey, dateObj) => {
      if (!dateKey) return false;
      const [y, m] = dateKey.split('-').map(Number);
      return y === dateObj.getFullYear() && m === dateObj.getMonth() + 1;
    };

    async function renderDiaryDetail() {
      if (!diaryDetailEl) return;
      diaryDetailEl.innerHTML = '';

      const detailHeader = document.createElement('div');
      detailHeader.className = 'diary-detail-header';

      const headerInfo = document.createElement('div');
      const dateEl = document.createElement('div');
      dateEl.className = 'diary-date';
      dateEl.textContent = selectedDateKey || '날짜를 선택하세요';
      const tagEl = document.createElement('div');
      tagEl.className = 'diary-tag';
      tagEl.textContent = selectedDateKey && diaryEntries[selectedDateKey]?.tag ? diaryEntries[selectedDateKey].tag : '#미선택';

      headerInfo.appendChild(dateEl);
      headerInfo.appendChild(tagEl);

      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'close-btn';
      closeBtn.textContent = '×';
      closeBtn.addEventListener('click', () => {
        selectedDateKey = null;
        renderDiaryDetail();
        renderCalendar();
      });

      detailHeader.appendChild(headerInfo);
      detailHeader.appendChild(closeBtn);
      diaryDetailEl.appendChild(detailHeader);

      const contentEl = document.createElement('div');
      contentEl.className = 'diary-content';

      if (!selectedDateKey) {
        const info = document.createElement('p');
        info.textContent = '달력에서 날짜를 눌러 기록을 확인하세요.';
        contentEl.appendChild(info);
      } else {
        // Load diary content from backend
        const hasEntry = !!diaryEntries[selectedDateKey];
        const diaryContent = hasEntry ? await loadDiaryDetail(selectedDateKey) : null;

        if (diaryContent) {
          const lines = diaryContent.split('\n');
          lines.forEach((line) => {
            if (line.trim()) {
              const p = document.createElement('p');
              p.textContent = line;
              contentEl.appendChild(p);
            }
          });
        } else {
          const empty = document.createElement('p');
          empty.textContent = '기록이 없습니다. 새로운 기억을 남겨주세요.';
          contentEl.appendChild(empty);
        }
      }

      diaryDetailEl.appendChild(contentEl);
    }

    function renderCalendar() {
      if (!calendarGridEl) return;
      calendarGridEl.innerHTML = '';

      ['일', '월', '화', '수', '목', '금', '토'].forEach((day) => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        calendarGridEl.appendChild(header);
      });

      const firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).getDay();
      const daysInMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0).getDate();

      for (let i = 0; i < firstDay; i += 1) {
        const empty = document.createElement('div');
        empty.className = 'calendar-day';
        calendarGridEl.appendChild(empty);
      }

      for (let day = 1; day <= daysInMonth; day += 1) {
        const dateKey = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const entry = diaryEntries[dateKey];
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';

        if (entry) dayEl.classList.add('has-entry');
        if (selectedDateKey === dateKey) dayEl.classList.add('selected');

        const numberEl = document.createElement('span');
        numberEl.className = 'calendar-day-number';
        numberEl.textContent = String(day);
        dayEl.appendChild(numberEl);

        if (entry?.emoji) {
          const iconEl = document.createElement('span');
          iconEl.className = 'calendar-day-icon';
          iconEl.textContent = entry.emoji;
          dayEl.appendChild(iconEl);
        }

        dayEl.addEventListener('click', () => {
          selectedDateKey = dateKey;
          renderCalendar();
        });

        calendarGridEl.appendChild(dayEl);
      }

      renderDiaryDetail();
    }

    function changeMonth(offset) {
      currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + offset, 1);
      if (!selectedDateKey || !isSameMonth(selectedDateKey, currentMonth)) {
        const monthEntries = Object.keys(diaryEntries).filter((key) => isSameMonth(key, currentMonth)).sort();
        selectedDateKey = monthEntries[0] || formatDateKey(currentMonth);
      }
      if (monthTitleEl) monthTitleEl.textContent = formatMonthTitle(currentMonth);
      renderCalendar();
    }

    monthButtons.forEach((btn) => {
      btn.addEventListener('click', () => changeMonth(Number(btn.dataset.changeMonth || 0)));
    });

    if (monthTitleEl) monthTitleEl.textContent = formatMonthTitle(currentMonth);

    // Signup checklist & progress
    async function loadChecklist() {
      if (checklistLoaded || !checklistContainer) return;
      try {
        const response = await fetch('/static/data/user_profile_checklist.csv');
        const text = await response.text();
        const lines = text.trim().split('\n');
        if (lines.length <= 1) throw new Error('No checklist data');
        lines.shift(); // header
        const splitCsv = (line) => line.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/).map((s) => s.replace(/^"|"$/g, ''));
        lines.forEach((line) => {
          const cols = splitCsv(line);
          if (cols.length < 6) return;
          const [question_id, section, category, question_kr, input_type, options_kr] = cols;
          checklistData.push({ question_id, section, category, question_kr, input_type, options_kr });
        });
        checklistTotal = checklistData.length + 2; // id + pw + checklist items
        renderChecklist();
        checklistLoaded = true;
        updateProgress();
      } catch (err) {
        console.error('Checklist load failed', err);
        checklistContainer.innerHTML = '<p class="checklist-error">체크리스트를 불러오지 못했습니다.</p>';
      }
    }

    function renderChecklist() {
      if (!checklistContainer) return;
      checklistContainer.innerHTML = '';
      checklistData.forEach((item) => {
        const field = document.createElement('div');
        field.className = 'checklist-item';
        const label = document.createElement('label');
        const badge = document.createElement('span');
        badge.className = 'checklist-badge';
        badge.textContent = item.category || '';
        const qText = document.createElement('div');
        qText.className = 'checklist-question';
        qText.textContent = item.question_kr || item.question_id;
        label.appendChild(badge);
        label.appendChild(qText);
        field.appendChild(label);

        if (item.input_type === 'single_choice' && item.options_kr) {
          const opts = item.options_kr.split(';');
          const hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = item.question_id;
          field.appendChild(hidden);

          const list = document.createElement('div');
          list.className = 'checklist-options';
          opts.forEach((opt) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'option-button';
            btn.textContent = opt.trim();
            btn.addEventListener('click', () => {
              hidden.value = opt.trim();
              list.querySelectorAll('.option-button').forEach((b) => b.classList.remove('selected'));
              btn.classList.add('selected');
              updateProgress();
            });
            list.appendChild(btn);
          });
          field.appendChild(list);
        } else {
          const input = document.createElement('input');
          input.type = 'text';
          input.name = item.question_id;
          input.placeholder = '답변을 입력하세요';
          input.addEventListener('input', updateProgress);
          field.appendChild(input);
        }

        checklistContainer.appendChild(field);
      });
    }

    signupForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(signupForm);
      const username = (formData.get('signup_username') || '').toString().trim();
      const password = (formData.get('signup_password') || '').toString().trim();

      if (!username || !password) {
        alert('아이디와 비밀번호를 입력해주세요.');
        return;
      }

      // 체크리스트 데이터 수집
      const checklist_data = {};
      checklistData.forEach((item) => {
        const value = formData.get(item.question_id);
        if (value && value.trim()) {
          checklist_data[item.question_id] = value.trim();
        }
      });

      try {
        // 백엔드 API로 회원가입 요청
        const response = await fetch('/api/signup/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: username,
            password: password,
            email: '',  // 이메일 필드 추가 시 수정
            checklist_data: checklist_data
          })
        });

        const data = await response.json();

        if (data.success) {
          alert(data.message || '회원가입이 완료되었습니다!');
          state.isLoggedIn = true;
          state.userName = username;
          renderAuth();
          switchPage('home');
        } else {
          alert(data.message || '회원가입에 실패했습니다.');
        }
      } catch (error) {
        console.error('Signup error:', error);
        alert('회원가입 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
    });

    function updateProgress() {
      if (!progressBar || !progressText) return;
      const inputs = [
        ...(signupForm?.querySelectorAll('input[name="signup_username"], input[name="signup_password"]') || []),
        ...(checklistContainer?.querySelectorAll('input') || [])
      ];
      let answered = 0;
      inputs.forEach((el) => {
        if (el.type === 'hidden') {
          if (el.value && el.value.trim()) answered += 1;
        } else if (el.type === 'text' || el.type === 'password') {
          if (el.value && el.value.trim()) answered += 1;
        }
      });
      const percent = checklistTotal ? Math.min(100, Math.round((answered / checklistTotal) * 100)) : 0;
      progressBar.style.width = `${percent}%`;
      progressText.textContent = `${percent}% 완료`;
    }

    window.addEventListener('resize', () => moveNavIndicator());

    initAskSwiper();
    renderAuth();
    switchPage(state.currentPage);
    state.selectedServiceType = null;
    generateDiaryBtn?.addEventListener('click', generateDiary);
  });

}
