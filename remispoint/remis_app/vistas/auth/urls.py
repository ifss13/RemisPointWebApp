from django.urls import path
from . import *

urlpatterns = [
    path("login/", vista_login, name="login"),
    path('logout/', custom_logout, name='logout'),
    path("registro/", register, name="registro"),
    path("cuenta/cambiar-contrasena", cambiar_contrasena, name="cambiar_contrasena"),
]
