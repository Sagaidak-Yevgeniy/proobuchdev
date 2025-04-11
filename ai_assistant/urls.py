from django.urls import path
from . import views

urlpatterns = [
    path('chat/<int:session_id>/', views.chat_detail, name='chat_detail'),
    path('chat/new/', views.chat_new, name='chat_new'),
    path('chat/new/<str:context_type>/<int:context_id>/', views.chat_new_with_context, name='chat_new_with_context'),
    path('chat/<int:session_id>/send/', views.chat_send_message, name='chat_send_message'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/<int:session_id>/feedback/<int:message_id>/', views.chat_feedback, name='chat_feedback'),
    path('chat/<int:session_id>/delete/', views.chat_delete, name='chat_delete'),
]