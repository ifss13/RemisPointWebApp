from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from remis_app.models import Viaje
from django.http import JsonResponse

@login_required
def verificar_estado_viaje(request, id_viaje):
    """Devuelve el estado actual del viaje para actualizar dinámicamente la interfaz del cliente."""
    viaje = get_object_or_404(Viaje, id_viaje=id_viaje)

    return JsonResponse({"estado": viaje.estado})