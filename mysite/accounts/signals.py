from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(pre_social_login)
def link_to_existing_user(sender, request, sociallogin, **kwargs):
    # Получаем email от Google
    email = sociallogin.account.extra_data.get('email')
    if email:
        try:
            # Пытаемся найти пользователя с таким email
            user = User.objects.get(email=email)
            # Связываем текущий sociallogin с существующим пользователем
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # Если пользователя нет — ничего не делаем, создастся новый
            pass