
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from remis_app.models import Cliente, Chofer, ChoferAuto
import json

@csrf_exempt
def actualizar_estado_chofer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            disponible = data.get("disponible", False)

            # Obtener el cliente basado en el correo del usuario autenticado
            cliente = Cliente.objects.filter(correo=request.user.email).first()
            if not cliente:
                return JsonResponse({"status": "error", "message": "Cliente no encontrado."})

            # Obtener el chofer relacionado con el cliente
            chofer = Chofer.objects.filter(id_cliente=cliente).first()
            if not chofer:
                return JsonResponse({"status": "error", "message": "Chofer no encontrado."})

            # Obtener el ChoferAuto relacionado con el chofer
            chofer_auto = ChoferAuto.objects.filter(id_chofer=chofer).first()
            if not chofer_auto:
                return JsonResponse({"status": "error", "message": "No se encontró un registro en ChoferAuto para este chofer."})

            # Actualizar disponibilidad
            chofer_auto.disponibilidad = disponible
            chofer_auto.save()

            return JsonResponse({"status": "success", "message": "Estado actualizado correctamente"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)