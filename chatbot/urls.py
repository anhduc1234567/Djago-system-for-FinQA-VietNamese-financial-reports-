# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL cho trang chat, nhận conversation_id (có thể optional)
    path('', views.chat_home, name='chat_home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('new/', views.new_chat, name='new_chat'), 
    path('<str:conversation_id>/', views.chat_home, name='chat_home'),
    path('chat/<str:conversation_id>/', views.chat_home, name='chat_home'),
    path('delete/<str:conversation_id>/', views.delete_chat, name='delete_chat'),
    path("<str:conversation_id>/send/", views.chat_send, name="chat_send"),  # gửi message

]