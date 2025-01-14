from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from remis_app.views import base_pedidos, no_autorizado

urlpatterns = [
    path('registro/', views.register, name='registro'),
    path('home/', views.home, name='home'),  # Página de inicio
    path('', views.home, name='home'),  # Página de inicio si el usuario va a la raíz
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('calcular_ruta/', views.calcular_ruta, name='calcular_ruta'),
    path('verificar_sesion/', views.verificar_sesion, name='verificar_sesion'),
    path('geocodificar-inversa/', views.geocodificar_inversa, name='geocodificar_inversa'),
    path("pedidos/", views.pedidos, name="pedidos"),
    path('asignar-pedidos/', views.asignar_pedidos, name='asignar_pedidos'),  # Ruta para la página de asignación,
    path('finalizar-viaje/<int:id_viaje>/', views.finalizar_viaje, name='finalizar_viaje'),
    path('cuenta/', views.panel_cuenta, name='panel_cuenta'),
    path('cuenta/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('no_autorizado/', no_autorizado, name='no_autorizado'),
    path('esperando_chofer/<int:pedido_id>/', views.esperando_chofer, name='esperando_chofer'),  # Asegúrate de que esta URL esté definida
    path('verificar_estado_pedido/<int:pedido_id>/', views.verificar_estado_pedido, name='verificar_estado_pedido'),
    path('obtener_notificaciones/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('marcar_como_leida/<int:id>/', views.marcar_como_leida, name='marcar_como_leida'),
    path('remiseria/', views.remiserias, name='remiseria'),
]