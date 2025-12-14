from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    회원가입 체크리스트 기반 사용자 프로필 모델
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # === 기본 정보 (Section: basic) ===
    # A1: 이름/호칭
    preferred_name = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="호칭/별칭",
        help_text="사용자가 선호하는 이름이나 호칭"
    )
    
    # A2: 움직임/기동성
    MOBILITY_CHOICES = [
        ('comfortable_walking', '걷기가 비교적 편하다'),
        ('slow_walking', '천천히라면 걷기는 가능하다'),
        ('indoor_only', '실내에서만 주로 움직인다'),
        ('mostly_lying', '대부분 누워 지낸다'),
    ]
    mobility_status = models.CharField(
        max_length=30,
        choices=MOBILITY_CHOICES,
        blank=True,
        verbose_name="움직임/기동성",
        help_text="평소 이동이나 움직임 정도"
    )
    
    # === 감정 정보 (Section: emotion) ===
    # B1: 현재 마음
    EMOTION_CHOICES = [
        ('anxious', '불안하다'),
        ('lethargic', '무기력하다'),
        ('lonely', '외롭다'),
        ('confused', '혼란스럽다'),
        ('sad', '슬프다'),
        ('peaceful', '그래도 꽤 평온하다'),
        ('hard_to_express', '말로 표현하기 어렵다'),
    ]
    current_emotion = models.CharField(
        max_length=30,
        choices=EMOTION_CHOICES,
        blank=True,
        verbose_name="현재 마음 상태",
        help_text="요즘 마음 상태를 한 단어로 표현"
    )
    
    # === 향후 확장을 위한 추가 필드 ===
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="생년월일"
    )
    
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('O', '기타'),
        ('N', '밝히고 싶지 않음'),
    ]
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name="성별"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="연락처"
    )
    
    # 추가 체크리스트 데이터를 JSON으로 저장 (향후 필드 확장용)
    additional_checklist_data = models.TextField(
        default="{}", 
        blank=True,
        verbose_name="추가 체크리스트 데이터",
        help_text="JSON 형태로 저장되는 추가 정보"
    )
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    
    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}의 프로필"
    
    def get_display_name(self):
        """표시용 이름 반환 (preferred_name이 있으면 그것을, 없으면 username)"""
        return self.preferred_name if self.preferred_name else self.user.username