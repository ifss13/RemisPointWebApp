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
from remis_app.models import PedidosCliente, ChoferAuto, Cliente, Viaje, Chofer, Auto, Notificacion
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from remis_app.decorador import base_required
from django.views.decorators.csrf import csrf_exempt

ORS_API_KEY = '5b3ce3597851110001cf6248bbaa88fc959c42db9efc751597c03a47'

def register(request):
    if request.method == "POST":
        # Obtener los datos del formulario
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        username = request.POST['username']
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

        # Verificación de si el correo o el username ya existen
        if User.objects.filter(email=correo).exists():
            return render(request, 'registro.html', {'error': "Este correo ya está registrado", 'localidades': Localidad.objects.all()})
        if User.objects.filter(username=username).exists():
            return render(request, 'registro.html', {'error': "El nombre de usuario ya está registrado", 'localidades': Localidad.objects.all()})

        try:
            # Crear un nuevo usuario en Django (tabla auth_user)
            user = User.objects.create_user(
                username=username,
                password=password,
                email=correo,
                first_name=nombre,
                last_name=apellido
            )

            # Relacionar con la tabla de clientes
            localidad_obj = Localidad.objects.get(id_localidad=localidad)
            cliente = Cliente(
                nombre=nombre,
                apellido=apellido,
                username=username,
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
            pedido = PedidosCliente.objects.create(
                id_cliente=cliente,
                dir_salida=dir_salida,
                dir_destino=dir_destino,
                estado_pedido="Pendiente"
            )

            # Devolver la URL a la que se debe redirigir el cliente
            return JsonResponse({"status": "success", "redirect_url": f"/esperando_chofer/{pedido.id_pedido}/"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    elif request.method == "GET":
        return render(request, "pedidos.html")

    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)


@login_required
def esperando_chofer(request, pedido_id):
    # Obtener el pedido del cliente
    pedido = PedidosCliente.objects.get(id_pedido=pedido_id)

    if pedido.estado_pedido == "Asignado":
        # Buscar el viaje asignado a este pedido, y que el estado sea "En Viaje"
        viaje = Viaje.objects.filter(id_cliente=pedido.id_cliente, estado="En Viaje").first()  # Seleccionamos el primer viaje en estado "En Viaje"

        if viaje:
            # Obtener la patente del auto desde el viaje
            patente_auto = viaje.patente

            # Buscar la relación del chofer con el auto
            chofer_auto = ChoferAuto.objects.filter(patente=patente_auto, disponibilidad=True).first()

            if chofer_auto:
                # Obtener los datos del chofer
                chofer = Chofer.objects.get(id_chofer=chofer_auto.id_chofer)
                
                # Obtener los datos del auto
                auto = Auto.objects.get(patente=patente_auto)

                # Renderizar la página con los datos del chofer y el auto
                return render(request, 'chofer_asignado.html', {
                    'pedido': pedido,
                    'chofer': chofer,
                    'auto': auto,
                })
            else:
                # En caso de que no haya un chofer disponible
                return render(request, 'esperando_chofer.html', {'pedido': pedido})
        else:
            # Si no se encuentra un viaje en estado "En Viaje"
            return render(request, 'esperando_chofer.html', {'pedido': pedido})
    else:
        # Si el pedido aún está pendiente, mostrar el spinner
        return render(request, 'esperando_chofer.html', {'pedido': pedido})

@login_required
def verificar_estado_pedido(request, pedido_id):
    try:
        pedido = PedidosCliente.objects.get(id_pedido=pedido_id)
        
        if pedido.estado_pedido == "Pendiente":
            return JsonResponse({'estado_pedido': 'Pendiente'})
        
        elif pedido.estado_pedido == "Asignado":
            viaje = Viaje.objects.get(id_cliente=pedido.id_cliente, estado='Asignado')
            auto = Auto.objects.get(patente=viaje.patente)
            chofer_auto = ChoferAuto.objects.get(patente=viaje.patente)
            chofer = Chofer.objects.get(id_chofer=chofer_auto.id_chofer)
            
            return JsonResponse({
                'estado_pedido': 'Asignado',
                'chofer': {
                    'nombre': chofer.nombre,
                    'telefono': chofer.telefono
                },
                'auto': {
                    'modelo': auto.modelo,
                    'patente': auto.patente
                }
            })
    except Exception as e:
        return JsonResponse({'estado_pedido': 'Error', 'message': str(e)}, status=500)

from django.utils import timezone

@base_required
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

            cliente = pedido.id_cliente  # Aquí estás obteniendo el cliente
            usuario = User.objects.get(email=cliente.correo)

            Notificacion.objects.create(
                usuario=usuario,  # Aquí pasas la instancia de 'User', no el correo
                mensaje="Tu viaje ha sido asignado, el chofer está en camino."
            )

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

@base_required
def base_pedidos(request):
    # Lógica de la vista para la página "base_pedidos"
    return render(request, 'base_pedidos.html')


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


@login_required
def panel_cuenta(request):
    # Obtener el cliente relacionado con el usuario logueado
    cliente = get_object_or_404(Cliente, correo=request.user.email)
    
    # Verificar si el cliente tiene tipo de cuenta 'base' (tipo_cuenta == 3)
    es_base = cliente.tipo_cuenta == 3  # Esto es True si el cliente es tipo 'base'
    
    # Obtener los viajes y pedidos del cliente
    viajes = Viaje.objects.filter(id_cliente=cliente.id_cliente)
    pedidos = PedidosCliente.objects.filter(id_cliente=cliente.id_cliente)

    # Pasar la variable 'es_base' a la plantilla para usarla en el frontend
    return render(request, 'panel_cuenta.html', {
        'cliente': cliente,
        'viajes': viajes,
        'pedidos': pedidos,
        'es_base': es_base,  # Aquí pasamos la variable
    })



@login_required
def cambiar_contrasena(request):
    """
    Vista para cambiar la contraseña del usuario en ambas tablas.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Cambiar la contraseña en auth_user
            user = form.save()
            update_session_auth_hash(request, user)  # Mantener la sesión activa tras cambiar la contraseña

            # Cambiar la contraseña en la tabla Clientes
            cliente = Cliente.objects.get(correo=request.user.email)  # Buscar al cliente por el correo del usuario
            cliente.password = user.password  # Actualizar el campo 'password' en la tabla Clientes
            cliente.save()

            # Responder con éxito en formato JSON
            return JsonResponse({
                'status': 'success',
                'message': 'Tu contraseña ha sido cambiada con éxito.'
            })
        else:
            # Si hay errores de validación, devolverlos en formato JSON
            return JsonResponse({
                'status': 'error',
                'message': 'Por favor corrige los errores a continuación.',
                'errors': form.errors
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        })


def no_autorizado(request):
    return render(request, 'no_autorizado.html', {'error': "No tienes permisos para acceder a esta página."})


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
        
