# remis_app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import Cliente, Localidad
from django.db import IntegrityError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import openrouteservice
from django.conf import settings
import requests
from .models import PedidosCliente
import json
from remis_app.models import PedidosCliente, ChoferAuto, Cliente, Viaje
from django.shortcuts import get_object_or_404

ORS_API_KEY = '5b3ce3597851110001cf6248bbaa88fc959c42db9efc751597c03a47'

def register(request):
    if request.method == "POST":
        # Obtener los datos del formulario
        nombre = request.POST['nombre']
        telefono = request.POST['telefono']
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        password = request.POST['password']
        password2 = request.POST['password2']
        localidad = request.POST['localidad']

        # Verificación de formato de correo
        if not correo or '@' not in correo:
            return render(request, 'registro.html', {'error': "Correo no válido", 'localidades': Localidad.objects.all()})

        # Verificación de contraseñas
        if password != password2:
            return render(request, 'registro.html', {'error': "Las contraseñas no coinciden", 'localidades': Localidad.objects.all()})

        # Verificación de si el correo ya existe
        if User.objects.filter(email=correo).exists():
            return render(request, 'registro.html', {'error': "Este correo ya está registrado", 'localidades': Localidad.objects.all()})

        try:
            # Crear un nuevo usuario en Django (esto será para clientes)
            user = User.objects.create_user(username=correo, password=password, email=correo)

            # Relacionar con la tabla de clientes
            localidad_obj = Localidad.objects.get(id_localidad=localidad)
            cliente = Cliente(
                nombre=nombre,
                telefono=telefono,
                direccion=direccion,
                correo=correo,
                password=password,
                id_localidad=localidad_obj,
                tipo_cuenta=Cliente.CLIENTE,
            )
            cliente.save()

            # Login del usuario después de la creación
            login(request, user)

            return redirect('home')  # Redirige a la página de inicio o donde quieras

        except IntegrityError:
            return render(request, 'registro.html', {'error': "Hubo un error al guardar los datos. Intenta nuevamente.", 'localidades': Localidad.objects.all()})

    # Si es GET, muestra el formulario de registro
    localidades = Localidad.objects.all()
    return render(request, 'registro.html', {'localidades': localidades})



# Vista para la página de inicio
def home(request):
    return render(request, 'home.html')  # Asegúrate de que el template 'home.html' exista


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirige al usuario si ya está autenticado

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirige a la página de inicio después de iniciar sesión
        else:
            # Si el formulario no es válido, se renderiza nuevamente el login
            return render(request, 'registration/login.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')

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

@login_required
def pedidos(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Leer los datos enviados por el frontend
            dir_salida = data.get("dir_salida")
            dir_destino = data.get("dir_destino")

            if not dir_salida or not dir_destino:
                return JsonResponse({"status": "error", "message": "Por favor completa ambos campos."}, status=400)

            # Obtener el cliente relacionado con el usuario actual
            cliente = get_object_or_404(Cliente, correo=request.user.email)

            # Crear el registro en la tabla PedidoCliente
            PedidosCliente.objects.create(
                id_cliente=cliente,
                dir_salida=dir_salida,
                dir_destino=dir_destino,
                estado_pedido="Pendiente"
            )
            return JsonResponse({"status": "success", "message": "Pedido registrado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # Manejo de solicitudes GET
    elif request.method == "GET":
        return render(request, "pedidos.html")  # Renderiza la plantilla para el formulario de pedidos

    # Otros métodos no permitidos
    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)

import datetime
from django.utils import timezone

def asignar_pedidos(request):
    if request.method == "GET":
        pedidos_pendientes = PedidosCliente.objects.filter(estado_pedido="Pendiente")
        choferes_disponibles = ChoferAuto.objects.filter(disponibilidad=True)
        viajes_en_viaje = Viaje.objects.filter(estado="En viaje")
        return render(request, "base_pedidos.html", {
            "pedidos": pedidos_pendientes,
            "choferes": choferes_disponibles,
            "viajes_en_viaje": viajes_en_viaje
        })

    elif request.method == "POST":
        try:
            id_pedido = request.POST.get("id_pedido")
            id_chofer = request.POST.get("id_chofer")

            if not id_pedido or not id_chofer:
                return JsonResponse({"status": "error", "message": "Datos incompletos."}, status=400)

            id_pedido = int(id_pedido)
            id_chofer = int(id_chofer)

            pedido = get_object_or_404(PedidosCliente, id_pedido=id_pedido)
            chofer_auto = get_object_or_404(ChoferAuto, id_chofer=id_chofer, disponibilidad=True)

            viaje = Viaje.objects.create(
                id_cliente=pedido.id_cliente,
                dir_salida=pedido.dir_salida,
                dir_destino=pedido.dir_destino,
                hora=timezone.now().time(),
                fecha=timezone.now().date(),
                id_precio=1,
                cod_tipo_pago=1,
                id_remiseria=1,
                inicio=timezone.now().time(),
                fin=timezone.now().time(),
                patente=chofer_auto.patente,
                estado="En viaje"
            )

            pedido.estado_pedido = "Asignado"
            pedido.save()
            chofer_auto.disponibilidad = False
            chofer_auto.save()

            # Obtener la lista actualizada de viajes
            viajes_con_chofer = Viaje.objects.filter(estado="En viaje")

            # Devuelves la respuesta con la lista actualizada
            return render(request, "base_pedidos.html", {
                "pedidos": PedidosCliente.objects.filter(estado_pedido="Pendiente"),
                "choferes": ChoferAuto.objects.filter(disponibilidad=True),
                "viajes_con_chofer": viajes_con_chofer,
                "mensaje": "Viaje asignado correctamente."
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)




def finalizar_viaje(request, id_viaje):
    try:
        # Obtener el viaje a través del ID
        viaje = get_object_or_404(Viaje, id_viaje=id_viaje)

        # Obtener el auto relacionado con el viaje
        auto = viaje.patente

        # Obtener el chofer asociado al auto
        chofer_auto = get_object_or_404(ChoferAuto, patente=auto, disponibilidad=False)

        # Cambiar el estado del viaje a 'Finalizado'
        viaje.estado = "Finalizado"
        viaje.save()

        # Cambiar la disponibilidad del chofer a True
        chofer_auto.disponibilidad = True
        chofer_auto.save()

        # Devolver una respuesta JSON exitosa
        return JsonResponse({"status": "success", "message": "Viaje finalizado correctamente."})

    except Exception as e:
        # En caso de error, devolver un mensaje de error
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
