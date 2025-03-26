from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from remis_app.models import Viaje, Cliente, Chofer, PedidosCliente
import json
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
import requests
import threading
import time

@csrf_exempt
@login_required
def cambiar_estado_viaje(request, id_viaje):
    if request.method == "POST":
        try:
            viaje = Viaje.objects.get(id_viaje=id_viaje)

            cliente = Cliente.objects.get(correo=request.user.email)
            chofer = Chofer.objects.get(id_cliente=cliente)

            if viaje.id_chofer != chofer:
                return JsonResponse({"success": False, "error": "No autorizado"}, status=403)

            data = json.loads(request.body)
            nuevo_estado = data.get("estado")
            print("Nuevo estado recibido:", nuevo_estado)

            if viaje.estado == "Asignado":
                pedido = PedidosCliente.objects.filter(
                    id_cliente=viaje.id_cliente,
                    estado_pedido="Esperando al chofer"
                ).first()

                if not pedido:
                    print("⚠️ Error: No se encontró un pedido en estado 'Esperando al chofer'")
                    return JsonResponse({"success": False, "error": "No se encontró un pedido activo para este cliente."}, status=404)

                print(f"✅ Pedido encontrado: {pedido}")
                pedido.estado_pedido = "Asignado"
                pedido.save()
                print("✅ Estado del pedido actualizado a 'Asignado'")

                mensaje = "El chofer está en camino"
                notificar_async(viaje.id_cliente.fcm_token, mensaje)

            if nuevo_estado == "En viaje":
                viaje.inicio = now().time()
                mensaje = "El chofer ha iniciado el viaje"
                notificar_async(viaje.id_cliente.fcm_token, mensaje)

            if nuevo_estado == "Finalizado":
                viaje.fin = now().time()
                mensaje = "Tu viaje ha sido finalizado. ¡Gracias por usar nuestro servicio!"
                notificar_async(viaje.id_cliente.fcm_token, mensaje)

            if nuevo_estado:
                t0 = time.time()
                viaje.estado = nuevo_estado
                viaje.save(update_fields=["estado", "inicio", "fin"])
                print("⏱ Tiempo de save():", round(time.time() - t0, 3), "s")
                # viaje.refresh_from_db()  # innecesario
                print("Estado actualizado en DB:", viaje.estado)
                return JsonResponse({"success": True, "message": "Estado actualizado correctamente"})
            else:
                return JsonResponse({"success": False, "error": "Estado no proporcionado"}, status=400)

        except Viaje.DoesNotExist:
            return JsonResponse({"success": False, "error": "Viaje no encontrado"}, status=404)
        except PedidosCliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "No se encontró un pedido activo para este cliente."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


# ✅ Notificación asincrónica para no bloquear la respuesta
def notificar_async(player_id, mensaje):
    threading.Thread(target=enviar_notificacion_cliente, args=(player_id, mensaje)).start()

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
        print("❌ Error enviando notificación:", str(e))
