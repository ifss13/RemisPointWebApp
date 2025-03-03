from django.urls import path
from . import *

urlpatterns = [ 
    path('enviar_notificacion', enviar_notificacion, name='enviar_notificacion'),  
]