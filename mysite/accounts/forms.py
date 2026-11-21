from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from allauth.socialaccount.forms import SignupForm


class CustomSocialSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, request):
        user = super().save(request)
        if self.sociallogin:
            print("EXTRA DATA FROM GOOGLE:", self.sociallogin.account.extra_data)
            if not user.email:
                user.email = self.sociallogin.account.extra_data.get('email', '')
                user.save()
        return user
    
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2']

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))