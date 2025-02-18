from django.urls import path
from . import *

urlpatterns = [
    path('administracion/', asignar_pedidos, name='administracion'),  # Base
    path('autos/', listar_autos, name='listar_autos'),  # Base
    path('autos/crear/',crear_auto, name='crear_auto'),  # Base
    path('autos/editar/<str:patente>/', editar_auto, name='editar_auto'),  # Base
    path('autos/eliminar/<str:patente>/', eliminar_auto, name='eliminar_auto'),  # Base
    path('choferes/', asignar_pedidos, name='listar_choferes'),  # Base
    path('choferes/crear/', asignar_pedidos, name='crear_chofer'),  # Base
    path('choferes/editar/<int:id_chofer>/', asignar_pedidos, name='editar_chofer'),  # Base
    path('choferes/eliminar/<int:id_chofer>/', asignar_pedidos, name='eliminar_chofer'),  # Base
    path('asignar-auto/', crear_asignacion, name='crear_asignacion'),  # Base
    path('eliminar-asignacion/<int:id_chofer>/<str:patente>/', eliminar_asignacion, name='eliminar_asignacion'),
]