import json
from datetime import datetime

from django.http import JsonResponse, HttpResponseNotAllowed, StreamingHttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import sys
import os
from django.middleware.csrf import get_token
# Add chatbot directory to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATBOT_DIR = os.path.join(BASE_DIR, 'chatbot')
sys.path.insert(0, CHATBOT_DIR)

from conversation_engine import ConversationEngine
from .member_manager import MemberManager

# Initialize conversation engine (singleton pattern)
conversation_engine = None

def get_conversation_engine():
    global conversation_engine
    if conversation_engine is None:
        conversation_engine = ConversationEngine()
    return conversation_engine



def index(request, page: str = "home"):
    """Serve the main landing page with the requested section active."""
    safe_page = page if page in {"home", "services", "chat", "diary"} else "home"
    
    # Ensure CSRF token cookie is set for frontend fetch requests
    get_token(request)
    
    # Prepare initial authentication state for frontend
    auth_state = {
        'isAuthenticated': request.user.is_authenticated,
        'username': '',
        'profile': None
    }
    
    if request.user.is_authenticated:
        auth_state['username'] = request.user.username
        
        # Get user profile if available
        try:
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                auth_state['profile'] = {
                    'username': request.user.username,
                    'preferred_name': profile.preferred_name or request.user.username,
                    'mobility_status': profile.mobility_status or '',
                    'current_emotion': profile.current_emotion or '',
                    'mobility_display': profile.get_mobility_status_display() if profile.mobility_status else '',
                    'emotion_display': profile.get_current_emotion_display() if profile.current_emotion else ''
                }
        except Exception as e:
            print(f"Profile load error: {e}")
    
    # Convert auth_state to JSON string for JavaScript
    auth_state_json = json.dumps(auth_state)
    
    response = render(request, "index.html", {
        "current_page": safe_page,
        "auth_state_json": auth_state_json
    })

    # 비로그인 사용자는 매 방문마다 새 user_uuid를 발급해 세션 간 기록을 연결하지 않음
    if not request.user.is_authenticated:
        engine = get_conversation_engine()
        user_uuid = engine.session_manager.generate_user_id()
        response.set_cookie("user_uuid", user_uuid)  # 세션 쿠키 (브라우저 닫으면 삭제)
    elif "user_uuid" not in request.COOKIES:
        # 로그인 사용자는 기존 쿠키가 없을 때만 발급
        engine = get_conversation_engine()
        user_uuid = engine.session_manager.generate_user_id()
        response.set_cookie("user_uuid", user_uuid)

    return response


@csrf_exempt
@require_http_methods(["POST"])
def chat_message(request):
    """
    Handle chat messages from frontend.
    Expects JSON: {"message": str, "mode": "chat" | "info", "service_type": str (optional)}
    Returns JSON: {"response": str, "error": str (optional)}
    """
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        mode = data.get("mode", "chat")  # "chat" or "info"
        service_type = data.get("service_type", "")  # For info mode context
        
        if not message:
            return JsonResponse({"error": "메시지가 비어있습니다."}, status=400)
        
        # Get conversation engine
        engine = get_conversation_engine()
        
        # Get user_id: prioritize authenticated user's username, fallback to cookie UUID
        if request.user.is_authenticated:
            user_id = request.user.username
        else:
            user_id = request.COOKIES.get("user_uuid")
            if not user_id:
                # Fallback: Generate via backend
                user_id = engine.session_manager.generate_user_id()
        
        # If info mode with service type, prepend context to first message
        if mode == "info" and service_type:
            # Map service types to Korean context
            service_context = {
                "funeral_facilities": "장례 시설",
                "support_policy": "지원 정책",
                "inheritance": "유산 상속",
                "digital_info": "디지털 개인 정보"
            }
            context = service_context.get(service_type, "")
            if context:
                message = f"[사용자가 '{context}' 정보를 요청함] {message}"
        
        # Process message through conversation engine
        response_generator = engine.process_user_message_stream(user_id, message, mode=mode)
        
        return StreamingHttpResponse(
            response_generator, 
            content_type='text/plain' # 단순 텍스트 스트림으로 전송
        )
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)
    except Exception as e:
        print(f"Chat error: {e}")
        return JsonResponse({"error": f"오류가 발생했습니다: {str(e)}"}, status=500)

@require_http_methods(["GET"])
def get_diaries(request):
    """
    Get all diary entries metadata for calendar display.
    Returns JSON: {"diaries": [{"date": "YYYY-MM-DD", "emoji": str, "tags": str, "preview": str}]}
    """
    try:
        user_id = request.COOKIES.get("user_uuid", "guest")
        
        # Get conversation engine to access diary manager
        engine = get_conversation_engine()
        diaries_metadata = engine.diary_manager.list_diaries(user_id)
        
        return JsonResponse({"diaries": diaries_metadata})
    
    except Exception as e:
        print(f"Get diaries error: {e}")
        return JsonResponse({"error": f"다이어리 조회 중 오류가 발생했습니다: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_diary_detail(request, date):
    """
    Get detailed diary content for a specific date.
    Returns JSON: {"date": str, "content": str}
    """
    try:
        user_id = request.COOKIES.get("user_uuid", "guest")
        
        # Get conversation engine to access session manager
        engine = get_conversation_engine()
        diary_content = engine.session_manager.get_diary_entry(user_id, date)
        
        if not diary_content:
            return JsonResponse({"date": date, "content": ""})
        
        return JsonResponse({"date": date, "content": diary_content})
    
    except Exception as e:
        print(f"Get diary detail error: {e}")
        return JsonResponse({"error": f"다이어리 조회 중 오류가 발생했습니다: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_diary(request):
    """
    Generate diary from today's conversations.
    Returns JSON: {"success": bool, "diary": str, "message": str}
    """
    try:
        user_id = request.COOKIES.get("user_uuid", "guest")

        try:
            engine = get_conversation_engine()
        except Exception as e:
            # 엔진 초기화(LLM 키 등) 실패 시 바로 안내
            return JsonResponse({
                "success": False,
                "error": f"대화 엔진 초기화 오류: {str(e)}"
            }, status=200)

        # Generate diary
        diary_result = engine.generate_diary_summary(user_id)

        if "다이어리를 생성하지 않았습니다" in diary_result or "생성할 수 없습니다" in diary_result:
            return JsonResponse({
                "success": False,
                "message": diary_result
            })
        
        return JsonResponse({
            "success": True,
            "diary": diary_result,
            "message": "다이어리가 생성되었습니다."
        })
    
    except Exception as e:
        print(f"Generate diary error: {e}")
        return JsonResponse({
            "success": False,
            "error": f"다이어리 생성 중 오류가 발생했습니다: {str(e)}"
        }, status=500)

member_manager = MemberManager()


@csrf_exempt
@require_http_methods(["POST"])
def signup_api(request):
    """
    회원가입 API
    Expects JSON: {
        "username": str,
        "password": str,
        "email": str (optional),
        "checklist_data": {
            "A1": str,  // 호칭/이름
            "A2": str,  // 움직임/기동성
            "B1": str,  // 현재 마음
            ...
        }
    }
    Returns JSON: {"success": bool, "message": str}
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        checklist_data = data.get('checklist_data', {})
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '아이디와 비밀번호를 입력해주세요.'
            }, status=400)
        
        # member_manager를 통해 회원가입 처리
        result = member_manager.register_member(
            request,
            username=username,
            password=password,
            email=email,
            checklist_data=checklist_data
        )
        
        # Unpack result (now returns 3 values: success, message, profile_data)
        if len(result) == 3:
            success, message, profile_data = result
        else:
            # Fallback for old return format
            success, message = result
            profile_data = None
        
        status_code = 200 if success else 400
        response_data = {
            'success': success,
            'message': message
        }
        
        # Add profile data if signup succeeded
        if success and profile_data:
            response_data['profile'] = profile_data
        
        return JsonResponse(response_data, status=status_code)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '잘못된 JSON 형식입니다.'
        }, status=400)
    except Exception as e:
        print(f"Signup error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'회원가입 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """
    로그인 API
    Expects JSON: {
        "username": str,
        "password": str
    }
    Returns JSON: {
        "success": bool,
        "message": str,
        "profile": {
            "username": str,
            "preferred_name": str,
            "mobility_status": str,
            "current_emotion": str,
            "mobility_display": str,
            "emotion_display": str
        } (only on success)
    }
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '아이디와 비밀번호를 입력해주세요.'
            }, status=400)
        
        # member_manager를 통해 로그인 처리
        result = member_manager.login_member(
            request,
            username=username,
            password=password
        )
        
        # Unpack result (now returns 3 values)
        if len(result) == 3:
            success, message, profile_data = result
        else:
            # Fallback for old return format
            success, message = result
            profile_data = None
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'profile': profile_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=401)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '잘못된 JSON 형식입니다.'
        }, status=400)
    except Exception as e:
        print(f"Login error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'로그인 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


def signup_view(request):
    if request.method == 'POST':
        data = request.POST
        checklist_data = {
            # 폼 데이터에서 체크리스트 항목 추출
            'q1': data.get('q1'),
            'q2': data.get('q2'),
            # ...
        }
        success, message = member_manager.register_member(
            request,
            username=data.get('username'),
            password=data.get('password'),
            email=data.get('email'),
            checklist_data=checklist_data
        )
        if success:
            return redirect('login') # 로그인 페이지로 이동
        else:
            return render(request, 'signup.html', {'error': message})
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        data = request.POST
        result = member_manager.login_member(
            request,
            username=data.get('username'),
            password=data.get('password')
        )
        # Unpack result (now returns 3 values)
        if len(result) == 3:
            success, message, profile_data = result
        else:
            success, message = result
        
        if success:
            return redirect('home') # 메인 페이지로 이동
        else:
            return render(request, 'login.html', {'error': message})
    return render(request, 'login.html')


@csrf_exempt
@require_http_methods(["POST"])
def logout_api(request):
    """
    로그아웃 API
    Returns JSON: {"success": bool, "message": str}
    """
    try:
        # member_manager를 통해 로그아웃 처리
        success, message = member_manager.logout_member(request)
        
        response = JsonResponse({
            'success': success,
            'message': message
        })
        
        # user_uuid 쿠키 삭제하여 다음 로그인 시 새로운 세션 시작
        if success:
            response.delete_cookie('user_uuid')
        
        return response
        
    except Exception as e:
        print(f"Logout error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'로그아웃 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def withdraw_api(request):
    """
    회원탈퇴 API
    Returns JSON: {"success": bool, "message": str}
    """
    try:
        # 사용자 인증 확인
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': '로그인이 필요합니다.'
            }, status=401)
        
        # member_manager를 통해 회원탈퇴 처리
        success, message = member_manager.withdraw_member(request)
        
        status_code = 200 if success else 400
        return JsonResponse({
            'success': success,
            'message': message
        }, status=status_code)
        
    except Exception as e:
        print(f"Withdraw error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'회원탈퇴 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


def withdraw_view(request):
    if request.method == 'POST':
        success, message = member_manager.withdraw_member(request)
        if success:
            return redirect('home')
        else:
            return JsonResponse({'status': 'error', 'message': message})
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'})
