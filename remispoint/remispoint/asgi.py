import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from remis_app.routing import websocket_urlpatterns
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remispoint.settings')

# Configurar ASGI para manejar WebSockets y archivos estáticos
application = ProtocolTypeRouter({
    "http": ASGIStaticFilesHandler(get_asgi_application()),  # ✅ Esto maneja archivos estáticos en ASGI
    "websocket": URLRouter(websocket_urlpatterns),
})
