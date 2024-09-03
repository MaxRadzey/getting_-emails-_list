from django.urls import path

from .consumers import MyConsumer

websocket_urlpatterns = [
   path('ws/msg/', MyConsumer.as_asgi()),
]
