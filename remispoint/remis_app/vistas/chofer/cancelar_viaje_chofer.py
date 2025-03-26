from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from remis_app.models import Viaje, Cliente, Chofer
import requests

@csrf_exempt
@login_required
def cancelar_viaje_chofer(request, id_viaje):
    if request.method == "POST":
        try:
            cliente = Cliente.objects.get(correo=request.user.email)
            chofer = Chofer.objects.get(id_cliente=cliente)

            viaje = Viaje.objects.get(id_viaje=id_viaje)

            if viaje.id_chofer != chofer:
                return JsonResponse({"success": False, "error": "No autorizado"}, status=403)

            viaje.estado = "Cancelado por el chofer"
            viaje.save(update_fields=["estado"])

            # Notificar al cliente
            fcm_token = viaje.id_cliente.fcm_token
            enviar_notificacion_cliente(
                fcm_token,
                "Tu viaje fue cancelado por el chofer."
            )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


def enviar_notificacion_cliente(player_id, mensaje):
    url = "https://api.onesignal.com/notifications?c=push"
    payload = {
        "app_id": "0406f65d-0560-4e90-94f4-f2c3a52f61f4",
        "contents": {"en": mensaje},
        "include_player_ids": [player_id],
        "small_icon": "static/icons/auto_rp.ico",
    }
    headers = {
        "accept": "application/json",
        "Authorization": "Key os_v2_app_aqdpmxifmbhjbfhu6lb2kl3b6r3c6ek5xhqezpfknrevwobojg4mnvxnjkexfpodgle2qbsjcthqhblwyxtkciic7yo3xsktqwrfxfi",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("🔔 Notificación enviada:", response.status_code)
    except Exception as e:
        print("❌ Error al enviar notificación:", str(e))
