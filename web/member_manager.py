import os
import json
import logging
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

# 기존 모듈 임포트 (경로는 프로젝트 구조에 따라 조정 필요)
# models.py가 같은 앱 내에 있다고 가정
try:
    from .models import UserProfile 
except ImportError:
    # 모델이 없을 경우를 대비한 가상 클래스 (실제 적용 시 삭제)
    UserProfile = None 

# 챗봇 세션 관리자 임포트 (chatbot 폴더 내에 있다고 가정)
try:
    from chatbot.chatbot_modules.session_manager import SessionManager
except ImportError:
    # 경로가 다를 경우 상대 경로로 시도
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from chatbot_modules.session_manager import SessionManager

logger = logging.getLogger(__name__)

class MemberManager:
    """
    회원 가입, 로그인, 탈퇴 및 챗봇 세션 연동을 관리하는 클래스
    """
    def __init__(self):
        self.session_manager = SessionManager()

    def register_member(self, request, username, password, email, checklist_data):
        """
        [회원가입]
        1. Django User 생성
        2. 체크리스트 및 추가 정보 DB 저장 (UserProfile)
        3. 챗봇 세션 파일 초기화
        """
        if User.objects.filter(username=username).exists():
            return False, "이미 존재하는 아이디입니다."

        try:
            with transaction.atomic():
                # 1. 기본 유저 생성
                user = User.objects.create_user(username=username, password=password, email=email)
                
                # 2. 체크리스트 데이터 파싱
                # 체크리스트 항목을 개별 필드로 매핑
                mobility_mapping = {
                    '걷기가 비교적 편하다': 'comfortable_walking',
                    '천천히라면 걷기는 가능하다': 'slow_walking',
                    '실내에서만 주로 움직인다': 'indoor_only',
                    '대부분 누워 지낸다': 'mostly_lying',
                }
                
                emotion_mapping = {
                    '불안하다': 'anxious',
                    '무기력하다': 'lethargic',
                    '외롭다': 'lonely',
                    '혼란스럽다': 'confused',
                    '슬프다': 'sad',
                    '그래도 꽤 평온하다': 'peaceful',
                    '말로 표현하기 어렵다': 'hard_to_express',
                }
                
                # 체크리스트에서 값 추출
                preferred_name = checklist_data.get('A1', '')
                mobility_kr = checklist_data.get('A2', '')
                emotion_kr = checklist_data.get('B1', '')
                
                # 한글 값을 영문 코드로 변환
                mobility_status = mobility_mapping.get(mobility_kr, '')
                current_emotion = emotion_mapping.get(emotion_kr, '')
                
                # 3. UserProfile 생성 및 저장
                if UserProfile:
                    # 알려진 필드 외의 추가 데이터는 additional_checklist_data에 저장
                    known_fields = {'A1', 'A2', 'B1'}
                    additional_data = {k: v for k, v in checklist_data.items() if k not in known_fields}
                    
                    UserProfile.objects.create(
                        user=user,
                        preferred_name=preferred_name,
                        mobility_status=mobility_status,
                        current_emotion=current_emotion,
                        additional_checklist_data=json.dumps(additional_data, ensure_ascii=False)
                    )
                
                # 4. 챗봇 세션 파일 초기화 (빈 파일 생성)
                # 로그인 시 해당 username으로 파일을 로드할 수 있게 미리 생성해둡니다.
                self.session_manager.save_session(user.username, {
                    "user_profile": {
                        "name": preferred_name if preferred_name else username,
                        "username": username
                    },
                    "conversation_history": []
                })
                
                # 5. 회원가입 후 자동 로그인
                login(request, user)
                
                # 6. 프로필 데이터 준비 (프론트엔드 전달용)
                profile_data = {
                    'username': user.username,
                    'preferred_name': preferred_name or user.username,
                    'mobility_status': mobility_status or '',
                    'current_emotion': current_emotion or '',
                    'mobility_display': '',
                    'emotion_display': ''
                }
                
                # Get display values if UserProfile exists
                if UserProfile and hasattr(user, 'profile'):
                    try:
                        profile = user.profile
                        profile_data['mobility_display'] = profile.get_mobility_status_display() if profile.mobility_status else ''
                        profile_data['emotion_display'] = profile.get_current_emotion_display() if profile.current_emotion else ''
                    except Exception:
                        pass
                
                logger.info(f"회원가입 완료: {username} (호칭: {preferred_name})")
                return True, "회원가입이 완료되었습니다.", profile_data
                
        except Exception as e:
            logger.error(f"회원가입 중 오류 발생: {e}")
            return False, f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"

    def login_member(self, request, username, password):
        """
        [로그인]
        1. Django 인증
        2. 챗봇 세션 파일 존재 확인 및 로드 준비
        3. 사용자 프로필 정보 반환
        """
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 사용자 프로필 가져오기
            profile_data = {}
            try:
                if UserProfile and hasattr(user, 'profile'):
                    profile = user.profile
                    profile_data = {
                        'username': user.username,
                        'preferred_name': profile.preferred_name or user.username,
                        'mobility_status': profile.mobility_status or '',
                        'current_emotion': profile.current_emotion or '',
                        'mobility_display': profile.get_mobility_status_display() if profile.mobility_status else '',
                        'emotion_display': profile.get_current_emotion_display() if profile.current_emotion else ''
                    }
                else:
                    profile_data = {
                        'username': user.username,
                        'preferred_name': user.username,
                        'mobility_status': '',
                        'current_emotion': '',
                        'mobility_display': '',
                        'emotion_display': ''
                    }
            except Exception as e:
                logger.warning(f"프로필 로드 실패: {e}")
                profile_data = {
                    'username': user.username,
                    'preferred_name': user.username,
                    'mobility_status': '',
                    'current_emotion': '',
                    'mobility_display': '',
                    'emotion_display': ''
                }
            
            # 챗봇 세션 파일 확인 및 프로필 동기화
            session_data = self.session_manager.load_session(user.username)
            
            # DB 프로필을 세션에 동기화
            if 'user_profile' not in session_data:
                session_data['user_profile'] = {}
            
            session_data['user_profile'].update({
                'name': profile_data['preferred_name'],
                'username': user.username,
                'mobility': profile_data['mobility_display'],
                'emotion': profile_data['emotion_display']
            })
            
            # 세션 저장
            self.session_manager.save_profile(user.username, session_data)
            
            # 마지막 접속 시간 업데이트
            self.session_manager.update_last_visit(user.username)
            
            logger.info(f"로그인 성공: {username}")
            return True, "로그인되었습니다.", profile_data
        else:
            return False, "아이디 또는 비밀번호가 올바르지 않습니다.", None

    def logout_member(self, request):
        """
        [로그아웃]
        """
        if request.user.is_authenticated:
            # 로그아웃 전 마지막 상태 저장 (필요시)
            username = request.user.username
            self.session_manager.update_last_visit(username)
            
        logout(request)
        return True, "로그아웃되었습니다."

    def withdraw_member(self, request):
        """
        [회원탈퇴]
        1. DB에서 회원 정보 삭제 (Cascade)
        2. chatbot/sessions 파일 삭제
        """
        user = request.user
        if not user.is_authenticated:
            return False, "로그인 상태가 아닙니다."
            
        username = user.username
        
        try:
            with transaction.atomic():
                # 1. DB 삭제
                # Django의 User를 삭제하면 연결된 UserProfile도 같이 삭제됨 (on_delete=models.CASCADE 설정 시)
                user.delete()
                
                # 2. 세션 디렉토리 전체 삭제 (프로필, 히스토리, 다이어리 모두 포함)
                user_dir = self.session_manager._get_user_dir(username)
                if os.path.exists(user_dir):
                    import shutil
                    shutil.rmtree(user_dir)
                    logger.info(f"세션 디렉토리 삭제: {user_dir}")
                
                logger.info(f"회원탈퇴 완료: {username}")
                return True, "회원탈퇴가 완료되었습니다."
                
        except Exception as e:
            logger.error(f"회원탈퇴 실패: {e}")
            return False, "탈퇴 처리 중 오류가 발생했습니다."