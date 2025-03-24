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
from .models import Rating, Viaje  

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

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from remis_app.models import Viaje, PedidosCliente, Chofer
from django.core.exceptions import ObjectDoesNotExist

@csrf_exempt
def cancelar_viaje_asignado(request, viaje_id):
    if request.method == "POST":
        try:
            print(f"🔍 Recibida solicitud de cancelación para viaje ID: {viaje_id}")

            # Buscar el viaje
            viaje = Viaje.objects.get(id_viaje=viaje_id)
            print(f"✅ Viaje encontrado: {viaje}")

            # Buscar el pedido asociado al cliente en estado "Esperando al chofer"
            pedido = PedidosCliente.objects.filter(
                id_cliente=viaje.id_cliente,
                estado_pedido="Esperando al chofer"
            ).first()

            if not pedido:
                print("⚠️ Error: No se encontró un pedido en estado 'Esperando al chofer' para este cliente")
                return JsonResponse({"success": False, "error": "No se encontró un pedido activo para este cliente."}, status=404)

            print(f"✅ Pedido encontrado: {pedido}")

            # Verificar si el chofer existe
            chofer = Chofer.objects.get(id_chofer=viaje.id_chofer.id_chofer)
            print(f"✅ Chofer encontrado: {chofer}")

            # Eliminar el viaje
            viaje.delete()
            print("✅ Viaje eliminado correctamente")

            # Cambiar el estado del pedido a "Pendiente" para que pueda ser reasignado
            pedido.estado_pedido = "Pendiente"
            pedido.save()
            print("✅ Estado del pedido actualizado a 'Pendiente'")

            # Marcar al chofer como "Disponible"
            chofer_auto = Chofer.objects.filter(id_chofer=chofer.id_chofer).first()
            if chofer_auto:
                chofer_auto.disponibilidad = True
                chofer_auto.save()
                print("✅ Chofer marcado como 'Disponible'")

            return JsonResponse({"success": True, "message": "Viaje cancelado correctamente."})

        except Viaje.DoesNotExist:
            print("⚠️ Error: El viaje no existe")
            return JsonResponse({"success": False, "error": "El viaje no existe."}, status=404)
        except PedidosCliente.DoesNotExist:
            print("⚠️ Error: El pedido no existe")
            return JsonResponse({"success": False, "error": "No se encontró un pedido en estado 'Esperando al chofer' para este cliente."}, status=404)
        except Chofer.DoesNotExist:
            print("⚠️ Error: El chofer no existe")
            return JsonResponse({"success": False, "error": "El chofer no existe."}, status=404)
        except Exception as e:
            print(f"⚠️ Error desconocido: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from .models import Viaje

def reportes_viajes(request):
    mes = int(request.GET.get('mes', datetime.now().month))
    anio = int(request.GET.get('anio', datetime.now().year))

    # Obtener el primer y último día del mes seleccionado
    primer_dia = datetime(anio, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(anio + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(anio, mes + 1, 1) - timedelta(days=1)

    # Filtrar viajes por mes y año
    viajes_mes = Viaje.objects.filter(fecha__year=anio, fecha__month=mes)
    total_viajes_mes = viajes_mes.count()
    total_recaudado_mes = viajes_mes.aggregate(Sum('id_precio__precio'))['id_precio__precio__sum'] or 0

    # Calcular viajes y recaudación por semana
    viajes_por_semana = []
    recaudacion_por_semana = []
    dia_actual = primer_dia
    while dia_actual <= ultimo_dia:
        fin_semana = dia_actual + timedelta(days=6)
        viajes_semana = Viaje.objects.filter(fecha__range=[dia_actual, fin_semana])
        viajes_por_semana.append(viajes_semana.count())
        recaudacion_por_semana.append(viajes_semana.aggregate(Sum('id_precio__precio'))['id_precio__precio__sum'] or 0)
        dia_actual = fin_semana + timedelta(days=1)

    return JsonResponse({
        'viajesSemana': sum(viajes_por_semana),
        'viajesMes': total_viajes_mes,
        'recaudacionSemana': sum(recaudacion_por_semana),
        'recaudacionMes': total_recaudado_mes,
    })

from django.http import JsonResponse
from .models import Viaje

def viajes_por_chofer(request, id_chofer):
    viajes = Viaje.objects.filter(id_chofer=id_chofer).order_by('-fecha')

    data = []
    for v in viajes:
        data.append({
            "fecha": v.fecha.strftime("%d/%m/%Y %H:%M"),
            "cliente": f"{v.id_cliente.nombre} {v.id_cliente.apellido}",
            "dir_salida": v.dir_salida,
            "dir_destino": v.dir_destino,
            "precio": f"${v.id_precio.precio}",
        })

    return JsonResponse({"data": data})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Chofer

def actualizar_datos_chofer(request, id_chofer):
    chofer = get_object_or_404(Chofer, id_chofer=id_chofer)

    if request.method == 'POST':
        if 'foto' in request.FILES:
            chofer.foto = request.FILES['foto']
        if 'licencia' in request.FILES:
            chofer.licencia = request.FILES['licencia']
        chofer.save()
        return redirect('panel_chofer')

    return redirect('templates/chofer/panel_chofer.html')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from remis_app.models import Remiseria
import json

@csrf_exempt
def verificar_codigo_remiseria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo_ingresado = data.get('codigo')

            remiseria = Remiseria.objects.filter(password=codigo_ingresado).first()
            if remiseria:
                request.session['id_remiseria'] = remiseria.id_remiseria
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


from django.template.loader import render_to_string
from django.http import JsonResponse
from remis_app.models import PedidosCliente, ChoferAuto

def actualizar_panel_base(request):
    id_remiseria = request.session.get("id_remiseria")

    if not id_remiseria:
        return JsonResponse({"error": "No se detectó remisería activa."}, status=400)

    # Filtrar pedidos pendientes y choferes disponibles por remisería
    pedidos = PedidosCliente.objects.filter(id_remiseria=id_remiseria, estado_pedido="Pendiente")
    choferes = ChoferAuto.objects.filter(id_chofer__id_remiseria=id_remiseria, disponibilidad=True)
    viajes = Viaje.objects.filter(
        id_remiseria=id_remiseria,
        estado__in=["Asignado", "En camino al cliente", "En viaje"]
    )

    # Renderizar los fragmentos de tabla
    html_pedidos = render_to_string("administracion_base/tabla_pedidos.html", {"pedidos": pedidos})
    html_choferes = render_to_string("administracion_base/tabla_chofer.html", {"choferes": choferes})
    html_pedidos_select = render_to_string("administracion_base/opciones_pedidos.html", {"pedidos": pedidos})
    html_choferes_select = render_to_string("administracion_base/opciones_choferes.html", {"choferes": choferes})
    html_viajes = render_to_string("administracion_base/tabla_viajes.html", {"viajes": viajes})


    return JsonResponse({
        "html_pedidos": html_pedidos,
        "html_choferes": html_choferes,
        "html_pedidos_select": html_pedidos_select,
        "html_choferes_select": html_choferes_select,
        "html_viajes": html_viajes
    })

