# remis_app/routing.py

from django.urls import path, re_path
from remis_app.consumer import TestConsumer, LocationConsumer

websocket_urlpatterns = [
    path('ws/test/', TestConsumer.as_asgi()),  # WebSocket en /ws/test/
    re_path(r'ws/location/$', LocationConsumer.as_asgi()),
]
