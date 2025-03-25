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
    path('superadmin/', include('remis_app.vistas.superadmin.urls')),
    path('enviar-notificacion/', views.enviar_notificacion, name='enviar_notificacion'),
    path('calificar-chofer/<int:id_viaje>/', views.calificar_chofer, name='calificar_chofer'),
    path('cancelar_viaje_asignado/<int:viaje_id>/', views.cancelar_viaje_asignado, name="cancelar_viaje_asignado"),
    path('reportes_viajes/', views.reportes_viajes, name='reportes_viajes'),
    path('viajes-chofer/<int:id_chofer>/', views.viajes_por_chofer, name='viajes_por_chofer'),
    path('actualizar-datos-chofer/<int:id_chofer>/', views.actualizar_datos_chofer, name='actualizar_datos_chofer'),
    path('verificar-codigo-remiseria/', views.verificar_codigo_remiseria, name='verificar_codigo_remiseria'),
    path("actualizar-panel-base/", views.actualizar_panel_base, name="actualizar_panel_base"),
    path('superadmin/', views.panel_superadmin, name='panel_superadmin'),
]



