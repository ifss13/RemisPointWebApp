from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from remis_app.models import Viaje, Cliente, Chofer
import requests

@csrf_exempt
@login_required
def cancelar_viaje_cliente(request, id_viaje):
    if request.method == "POST":
        try:
            cliente = Cliente.objects.get(correo=request.user.email)
            viaje = Viaje.objects.get(id_viaje=id_viaje)

            if viaje.id_cliente != cliente:
                return JsonResponse({"success": False, "error": "No autorizado"}, status=403)

            if viaje.estado in ["Finalizado", "Cancelado por el cliente", "Cancelado por el chofer", "Cancelado por la base"]:
                return JsonResponse({"success": False, "error": "El viaje ya fue cancelado o finalizado."}, status=400)

            viaje.estado = "Cancelado por el cliente"
            viaje.save(update_fields=["estado"])

            if viaje.id_chofer:
                chofer = viaje.id_chofer  # ✅ ya es el objeto
                fcm_token = chofer.id_cliente.fcm_token
                enviar_notificacion_onesignal(
                    fcm_token,
                    "🚫 Viaje cancelado",
                    f"El cliente canceló el viaje #{viaje.id_viaje}."
                )


            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


def enviar_notificacion_onesignal(player_id, titulo, mensaje):
    if not player_id:
        return

    requests.post(
        "https://api.onesignal.com/notifications?c=push",
        json={
            "app_id": "0406f65d-0560-4e90-94f4-f2c3a52f61f4",
            "include_player_ids": [player_id],
            "headings": {"en": titulo},
            "contents": {"en": mensaje},
            "small_icon": "static/icons/auto_rp.ico"
        },
        headers={
            "Authorization": "Key os_v2_app_aqdpmxifmbhjbfhu6lb2kl3b6r3c6ek5xhqezpfknrevwobojg4mnvxnjkexfpodgle2qbsjcthqhblwyxtkciic7yo3xsktqwrfxfi",
            "Content-Type": "application/json"
        }
    )
