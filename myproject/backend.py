from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailAuthBackend(ModelBackend):
    """
    이메일을 사용한 로그인 백엔드
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 이메일로 사용자 찾기
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
