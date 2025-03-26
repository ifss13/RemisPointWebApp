from django.urls import path
from . import *

urlpatterns = [
    path('finalizar-viaje/<int:id_viaje>/', finalizar_viaje, name='finalizar_viaje'), 
    path("verificar_viaje_asignado/", verificar_viaje_asignado, name="verificar_viaje_asignado"), 
    path("cambiar_estado_viaje/<int:id_viaje>/", cambiar_estado_viaje, name="cambiar_estado_viaje"),
    path("chofer", panel_chofer, name='chofer'),
    path("actualizar_estado_chofer/", actualizar_estado_chofer, name="actualizar_estado_chofer"),
    path('cancelar_viaje_chofer/<int:id_viaje>/', cancelar_viaje_chofer, name='cancelar_viaje_chofer'),
]