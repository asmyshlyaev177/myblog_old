from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from blog.models import myUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = myUser

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = myUser
