# remis_app/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import openrouteservice
from django.conf import settings
import requests
from remis_app.models import PedidosCliente, Auto, Notificacion
from django.shortcuts import get_object_or_404
from remis_app.decorador import base_required
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

ORS_API_KEY = '5b3ce3597851110001cf6248bbaa88fc959c42db9efc751597c03a47'

# Vista para la página de inicio
def home(request):
    return render(request, 'home.html')  # Asegúrate de que el template 'home.html' exista


@login_required
def calcular_ruta(request):
    if request.method == 'POST':
        origen = request.POST.get('punto_partida')
        destino = request.POST.get('entrega')

        # Inicializa el cliente de OpenRouteService
        client = openrouteservice.Client(key=ORS_API_KEY)

        try:
            # Geocodificación para obtener coordenadas
            coords_origen = client.pelias_search(origen)['features'][0]['geometry']['coordinates']
            coords_destino = client.pelias_search(destino)['features'][0]['geometry']['coordinates']

            # Calcula la ruta entre los puntos
            ruta = client.directions(
                coordinates=[coords_origen, coords_destino],
                profile='driving-car',
                format='geojson'
            )

            return JsonResponse({'ruta': ruta}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def verificar_sesion(request):
    # Si el usuario está autenticado, responde con un código 200
    return JsonResponse({'message': 'Autenticado'}, status=200)


def geocodificar_inversa(request):
    # Obtener las coordenadas desde la solicitud
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if lat and lon:
        # API de OpenRouteService
        url = f'https://api.openrouteservice.org/geocode/reverse'
        headers = {
            'Authorization': ORS_API_KEY
        }
        params = {
            'point.lon': lon,
            'point.lat': lat,
            'size': 1  # Número de resultados a obtener
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                direccion = data['features'][0]['properties']['label']
                return JsonResponse({'direccion': direccion})
            else:
                return JsonResponse({'error': 'Dirección no encontrada'}, status=404)
        else:
            return JsonResponse({'error': 'Error al comunicarse con OpenRouteService'}, status=500)

    return JsonResponse({'error': 'Coordenadas no válidas'}, status=400)


@base_required
def base_pedidos(request):
    # Recuperar autos registrados
    autos = Auto.objects.all()

    # Pasar los autos al template
    return render(request, 'administracion_base/base_pedidos.html', {'autos': autos})


def no_autorizado(request):
    return render(request, 'base/no_autorizado.html', {'error': "No tienes permisos para acceder a esta página."})

def obtener_notificaciones(request):
    if request.user.is_authenticated:
        # Obtener solo las notificaciones no leídas
        notificaciones = Notificacion.objects.filter(usuario=request.user, leida=False).order_by('-fecha_creacion')
        
        # Crear una lista de notificaciones con solo la información que necesitamos
        notificaciones_data = [{
            'id': notificacion.id,
            'mensaje': notificacion.mensaje,
            'fecha': notificacion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
        } for notificacion in notificaciones]

        return JsonResponse({'notificaciones': notificaciones_data}, status=200)

    return JsonResponse({'error': 'Usuario no autenticado'}, status=401)


@csrf_exempt  # Solo usa esto si decides deshabilitar el CSRF, aunque no se recomienda
def marcar_como_leida(request, id):
    if request.method == 'POST':
        try:
            # Obtener la notificación utilizando el id
            notificacion = Notificacion.objects.get(id=id)
            notificacion.leida = True
            notificacion.save()
            return JsonResponse({'success': True})
        except Notificacion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})
        

@login_required  
def obtener_api_key(request):
    return JsonResponse({"api_key": settings.ORS_API_KEY})

#Cliente
@csrf_exempt
def cancelar_pedido(request, pedido_id):
    if request.method == "POST":
        try:
            pedido = get_object_or_404(PedidosCliente, id_pedido=pedido_id)

            if pedido.estado_pedido == "Pendiente":
                pedido.estado_pedido = "Cancelado por el Cliente"
                pedido.save()
                return JsonResponse({"success": True, "estado_pedido": "Cancelado por el Cliente"})
            else:
                return JsonResponse({"success": False, "error": "No se puede cancelar un pedido en este estado."})

        except PedidosCliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Pedido no encontrado."}, status=404)
        
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)


import requests

import json



@csrf_exempt
def enviar_notificacion(request):
    if request.method == "POST":
        try:
            # Convertir el body de la petición en un diccionario
            data = json.loads(request.body)
            mensaje = data.get("mensaje")
            player_id = data.get("player_id")

            # Verificar que los valores no sean None
            if not mensaje or not player_id:
                return JsonResponse({"error": "Faltan datos"}, status=400)

            # URL y payload para OneSignal
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
            return JsonResponse(response.json())  # Devolver la respuesta de OneSignal

        except json.JSONDecodeError:
            return JsonResponse({"error": "Formato JSON inválido"}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)



from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Rating, Viaje  # Necesitamos Viaje para obtener el id_viaje

def calificar_chofer(request, id_viaje):
    viaje = get_object_or_404(Viaje, id_viaje=id_viaje)
    
    if request.method == "POST":
        calificacion = int(request.POST.get('calificacion', 0))
        comentario = request.POST.get('comentario', '')

        # Guardamos la calificación en la base de datos
        Rating.objects.create(
            id_viaje=viaje,
            id_chofer=viaje.id_chofer,
            id_cliente=viaje.id_cliente,
            calificacion=calificacion,
            comentario=comentario
        )
        return JsonResponse({"success": True, "message": "Calificación guardada correctamente."})

    return render(request, 'clientes/calificar_chofer.html', {'viaje': viaje})
