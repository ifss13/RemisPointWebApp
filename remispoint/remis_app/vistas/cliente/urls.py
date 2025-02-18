from django.urls import path
from . import *


urlpatterns = [
    path("pedidos/", pedidos, name="pedidos"),  
    path('cuenta/', panel_cuenta, name='panel_cuenta'),  
    path('esperando_chofer/<int:pedido_id>/', esperando_chofer, name='esperando_chofer'),  
    path('verificar_estado_pedido/<int:pedido_id>/', verificar_estado_pedido, name='verificar_estado_pedido'), 
    path('remiseria/', remiserias, name='remiseria'),  
    path('viaje/', viaje, name='viaje'),  
    path('obtener_precio/', obtener_precio, name='obtener_precio'),  
    path('obtener_id_precio/', obtener_id_precio, name='obtener_id_precio'),  
    path('verificar_estado_viaje/<int:id_viaje>/', verificar_estado_viaje, name='verificar_estado_viaje'),  
    path('pagos/<int:id_viaje>/', pagos, name='pagos'),  
]

