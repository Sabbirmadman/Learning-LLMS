from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, ChatMessageView ,ChatMessageStreamView

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
    path('chats/<int:chat_id>/messages/', ChatMessageView.as_view(), name='chat-messages'),
    path('chats/<int:chat_id>/messages/stream/', ChatMessageStreamView.as_view(), name='chat-messages-stream'),
]