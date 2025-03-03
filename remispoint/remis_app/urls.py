from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from remis_app.views import no_autorizado
import urllib.parse
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.home, name='home'),  # Página de inicio si el usuario va a la raíz
    path('calcular_ruta/', views.calcular_ruta, name='calcular_ruta'), #Inicio
    path('verificar_sesion/', views.verificar_sesion, name='verificar_sesion'), #Auth
    path('geocodificar-inversa/', views.geocodificar_inversa, name='geocodificar_inversa'), #Inicio / General
    path('no_autorizado/', no_autorizado, name='no_autorizado'), #Auth
    path('obtener_notificaciones/', views.obtener_notificaciones, name='obtener_notificaciones'), #Todos
    path('marcar_como_leida/<int:id>/', views.marcar_como_leida, name='marcar_como_leida'), #Todos
    path('obtener-api-key/', views.obtener_api_key, name='obtener_api_key'), 
    path("cancelar_pedido/<int:pedido_id>/", views.cancelar_pedido, name="cancelar_pedido"), 
    path("", include("remis_app.vistas.auth.urls")),
    path("", include("remis_app.vistas.cliente.urls")),
    path("", include("remis_app.vistas.chofer.urls")),
    path("", include("remis_app.vistas.base.urls")),
    path("", include("remis_app.vistas.mp_auth.urls")),
    path('enviar-notificacion/', views.enviar_notificacion, name='enviar_notificacion'),
    path('calificar-chofer/<int:id_viaje>/', views.calificar_chofer, name='calificar_chofer'),
]



