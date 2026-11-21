from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('owner-profile/', views.owner_profile, name='owner_profile'),
    path('user-profile/', views.user_profile, name='user_profile'),
]
