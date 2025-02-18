from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from remis_app.models import *


def finalizar_viaje(request, id_viaje):
    try:
        # Obtener el viaje a través del ID
        viaje = get_object_or_404(Viaje, id_viaje=id_viaje)

        # Obtener el chofer y el auto relacionados con el viaje
        id_chofer = viaje.id_chofer.id_chofer  # 🔹 Obtenemos el chofer directamente desde Viaje
        auto = viaje.patente  # 🔹 Obtenemos la patente desde Viaje

        # Obtener el ChoferAuto correspondiente a este chofer y auto
        chofer_auto = get_object_or_404(ChoferAuto, patente=auto, id_chofer=id_chofer)

        # Cambiar el estado del viaje a 'Finalizado'
        viaje.estado = "Cancelado por la Base"
        viaje.save()

        # Cambiar la disponibilidad del chofer a True
        chofer_auto.disponibilidad = True
        chofer_auto.save()

        # Devolver una respuesta JSON exitosa
        return JsonResponse({"status": "success", "message": "Viaje cancelado correctamente."})

    except Exception as e:
        # En caso de error, devolver un mensaje de error
        return JsonResponse({"status": "error", "message": str(e)}, status=500)