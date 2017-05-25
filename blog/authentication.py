from .models import MyUser as User


# Бэкэнды авторизации по логину и емайлу
class UsernameAuthBackend(object):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username.lower())
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailAuthBackend(object):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(email__iexact=username.lower())
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

