from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from remis_app.models import Viaje, Cliente, Chofer
import json
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
import requests  # Para enviar la notificación a OneSignal

@csrf_exempt
@login_required
def cambiar_estado_viaje(request, id_viaje):
    if request.method == "POST":
        try:
            # Obtener el viaje por ID
            viaje = Viaje.objects.get(id_viaje=id_viaje)

            # Validar que el usuario autenticado sea el chofer asignado
            cliente = Cliente.objects.get(correo=request.user.email)
            chofer = Chofer.objects.get(id_cliente=cliente)

            if viaje.id_chofer != chofer:
                return JsonResponse({"success": False, "error": "No autorizado"}, status=403)

            # Leer los datos enviados en la petición
            data = json.loads(request.body)
            nuevo_estado = data.get("estado")
            print("Nuevo estado recibido:", nuevo_estado)
            
            if nuevo_estado == "En camino al cliente":
                # Enviar notificación al cliente
                mensaje = "El chofer esta en camino"
                enviar_notificacion_cliente(viaje.id_cliente.fcm_token, mensaje)
            # Actualizar la hora de inicio cuando el viaje cambia a "En viaje"
            if nuevo_estado == "En viaje":
                viaje.inicio = now().time()
                # Enviar notificación al cliente
                mensaje = "El chofer ha iniciado el viaje"
                enviar_notificacion_cliente(viaje.id_cliente.fcm_token, mensaje)
                
            # Actualizar la hora de finalización cuando el viaje cambia a "Finalizado"
            if nuevo_estado == "Finalizado":
                viaje.fin = now().time()
                # Enviar notificación al cliente
                mensaje = "Tu viaje ha sido finalizado. ¡Gracias por usar nuestro servicio!"
                enviar_notificacion_cliente(viaje.id_cliente.fcm_token, mensaje)

            # Actualizar el estado del viaje
            if nuevo_estado:
                viaje.estado = nuevo_estado
                viaje.save(update_fields=["estado", "inicio", "fin"])
                # Refrescar el objeto desde la DB para confirmar la actualización
                viaje.refresh_from_db()
                print("Estado actualizado en DB:", viaje.estado)
                return JsonResponse({"success": True, "message": "Estado actualizado correctamente"})
            else:
                return JsonResponse({"success": False, "error": "Estado no proporcionado"}, status=400)

        except Viaje.DoesNotExist:
            return JsonResponse({"success": False, "error": "Viaje no encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

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

    # Enviar la notificación
    response = requests.post(url, json=payload, headers=headers)
    return response.json()  # Devolver la respuesta de OneSignal