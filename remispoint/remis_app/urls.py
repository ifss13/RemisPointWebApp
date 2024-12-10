from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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
]