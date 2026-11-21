from django.urls import path
from . import views

urlpatterns = [
    path('', views.housing, name='housing'),
    path('add/', views.add_house, name='add_house'),
    path('<int:pk>/', views.house_page, name='house_page'),
    path('<int:pk>/booking/', views.room_booking, name='room_booking'),
    path('<int:pk>/booking/success/', views.booking_success, name='booking_success'),
    path('<int:pk>/add_room/', views.add_room, name='add_room'),
    path('<int:pk>/edit_room/', views.edit_room, name='edit_room'),
    path('<int:pk>/delete_room/', views.delete_room, name='delete_room'),
    path('room/<int:pk>/', views.room_detail, name='room_detail'),
    path('<int:pk>/edit_house', views.edit_house, name='edit_house'),
    path('<int:pk>/delete_house', views.delete_house, name='delete_house'),
    path('<int:pk>/delete_house/confirm', views.delete_house_confirm, name='delete_house_confirm'),
    path('room/<int:pk>/toggle-active/', views.toggle_room_active, name='toggle_room_active'),
]
