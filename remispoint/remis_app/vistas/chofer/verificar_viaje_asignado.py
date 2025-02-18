from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from remis_app.models import Cliente, Chofer, Viaje

@login_required
def verificar_viaje_asignado(request):
    try:
        # Obtener el cliente autenticado
        cliente = Cliente.objects.get(correo=request.user.email)
        chofer = Chofer.objects.get(id_cliente=cliente)

        # Buscar si el chofer tiene un viaje en progreso (asignado o en camino)
        viaje = Viaje.objects.filter(id_chofer=chofer, estado__in=["Asignado", "En camino al cliente", "En viaje"]).first()

        if viaje:
            return JsonResponse({
                "asignado": True,
                "id_viaje": viaje.id_viaje,
                "dir_salida": viaje.dir_salida,
                "dir_destino": viaje.dir_destino,
                "estado": viaje.estado  # Enviar el estado actual del viaje
            })

        return JsonResponse({"asignado": False})

    except (Cliente.DoesNotExist, Chofer.DoesNotExist):
        return JsonResponse({"asignado": False, "error": "No se encontró el chofer"}, status=400)
    except Exception as e:
        return JsonResponse({"asignado": False, "error": str(e)}, status=500)