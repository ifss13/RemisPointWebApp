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
from remis_app.models import PedidosCliente, ChoferAuto, Cliente, Viaje, Chofer, Auto, Notificacion, Remiseria, TipoPago
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from remis_app.decorador import base_required
from django.views.decorators.csrf import csrf_exempt
from .forms import AutoForm

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
            # Leer los datos enviados por el frontend
            data = json.loads(request.body)
            dir_salida = data.get("dir_salida")
            dir_destino = data.get("dir_destino")

            remiseria_id = data.get('id_remiseria')  # Cambié de GET a POST

            # Verificar si remiseria_id está presente
            if remiseria_id is None:
                return JsonResponse({"status": "error", "message": "No se proporcionó el id de la remisería."}, status=400)

            # Intentar convertir remiseria_id a un entero
            try:
                remiseria_id = int(remiseria_id)
            except ValueError:
                return JsonResponse({"status": "error", "message": "El id de la remisería no es válido."}, status=400)

            # Validar que las direcciones estén presentes
            if not dir_salida or not dir_destino:
                return JsonResponse({"status": "error", "message": "Por favor completa ambos campos."}, status=400)

            # Obtener el cliente relacionado con el usuario actual
            cliente = get_object_or_404(Cliente, correo=request.user.email)

            # Obtener la instancia de Remiseria usando el id
            remiseria = get_object_or_404(Remiseria, id_remiseria=remiseria_id)

            # Crear el registro en la tabla PedidoCliente
            pedido = PedidosCliente.objects.create(
                id_cliente=cliente,
                dir_salida=dir_salida,
                dir_destino=dir_destino,
                estado_pedido="Pendiente",
                id_remiseria=remiseria  # Aquí asignas la instancia de Remiseria
            )

            # Devolver la URL a la que se debe redirigir el cliente
            return JsonResponse({"status": "success", "redirect_url": f"/esperando_chofer/{pedido.id_pedido}/"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    elif request.method == "GET":
        remiseria_id = request.GET.get('remiseria_id')  # Capturamos el remiseria_id de la URL
        return render(request, "pedidos.html", {'remiseria_id': remiseria_id})

    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)




@login_required
def esperando_chofer(request, pedido_id):
    try:
        pedido = get_object_or_404(PedidosCliente, id_pedido=pedido_id)
        viaje = Viaje.objects.filter(id_cliente=pedido.id_cliente).first()
        chofer = viaje.chofer if viaje else None
        auto = Auto.objects.filter(patente=viaje.patente).first() if viaje else None

        return render(request, 'esperando_chofer.html', {
            'pedido_id': pedido_id,
            'chofer': chofer,
            'auto': auto,
            'viaje_asignado': viaje is not None,
        })
    except Exception as e:
        return render(request, 'esperando_chofer.html', {
            'pedido_id': pedido_id,
            'error': f"Error: {str(e)}"
        })



@login_required
def verificar_estado_pedido(request, pedido_id):
    try:
        pedido = PedidosCliente.objects.get(id_pedido=pedido_id)

        if pedido.estado_pedido == "Pendiente":
            return JsonResponse({'estado_pedido': 'Pendiente'})

        elif pedido.estado_pedido == "Asignado":
            return JsonResponse({'estado_pedido': 'Asignado'})

    except PedidosCliente.DoesNotExist:
        return JsonResponse({'estado_pedido': 'Error', 'message': 'Pedido no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'estado_pedido': 'Error', 'message': str(e)}, status=500)




from django.utils import timezone


@base_required
def asignar_pedidos(request):
    if request.method == "GET":
        pedidos_pendientes = PedidosCliente.objects.filter(estado_pedido="Pendiente")
        choferes_disponibles = ChoferAuto.objects.filter(disponibilidad=True)
        viajes_en_viaje = Viaje.objects.filter(estado="En viaje")
        autos = Auto.objects.all()
        remiserias = Remiseria.objects.all()
        choferes = Chofer.objects.all()
        asignaciones = ChoferAuto.objects.select_related('patente', 'id_chofer')  # Datos de la tabla puente
        viajes_registrados = Viaje.objects.all()
        tipopago = TipoPago.objects.all()

        return render(request, "base_pedidos.html", {
            "pedidos": pedidos_pendientes,
            "choferes": choferes_disponibles,
            "viajes_en_viaje": viajes_en_viaje,
            "autos": autos,
            "remiserias": remiserias,
            "choferes_list": choferes,
            "asignaciones": asignaciones,
            "viajes_registrados": viajes_registrados,
            "tipopago": tipopago,  
        })


    elif request.method == "POST":
        operation = request.POST.get("operation")

        if not operation:
            return JsonResponse({"status": "error", "message": "Operación no especificada."}, status=400)

        # Crear asignación auto-chofer
        if operation == "asignar_auto":
            try:
                id_chofer = request.POST.get("id_chofer")
                patente = request.POST.get("patente")
                turno = request.POST.get("turno")

                chofer = get_object_or_404(Chofer, id_chofer=id_chofer)
                auto = get_object_or_404(Auto, patente=patente)

                ChoferAuto.objects.create(
                    id_chofer=chofer,
                    patente=auto,
                    turno=turno,
                    disponibilidad=True  # Por defecto disponible
                )

                messages.success(request, f"Auto {auto.patente} asignado a {chofer.nombre}.")
            except Exception as e:
                messages.error(request, f"Error al asignar auto: {str(e)}")
            return redirect("administracion")

        # Eliminar asignación auto-chofer
        elif operation == "eliminar_asignacion":
            try:
                id_chofer = request.POST.get("id_chofer")
                patente = request.POST.get("patente")

                asignacion = get_object_or_404(ChoferAuto, id_chofer=id_chofer, patente=patente)
                asignacion.delete()

                messages.success(request, f"Asignación entre {asignacion.id_chofer.nombre} y {asignacion.patente.patente} eliminada.")
            except Exception as e:
                messages.error(request, f"Error al eliminar asignación: {str(e)}")
            return redirect("administracion")

        # Manejar la edición de un auto
        elif operation == "editar_auto":
            try:
                patente = request.POST.get("patente")
                auto = get_object_or_404(Auto, patente=patente)

                auto.tipo = request.POST.get("tipo", auto.tipo)
                auto.anio_modelo = request.POST.get("anio_modelo", auto.anio_modelo)
                auto.propietario = request.POST.get("propietario", auto.propietario)
                auto.id_remiseria = request.POST.get("id_remiseria", auto.id_remiseria)
                if "foto" in request.FILES:
                    auto.foto = request.FILES["foto"]
                auto.save()

                messages.success(request, f"Auto {auto.patente} actualizado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al actualizar el auto: {str(e)}")
            return redirect("administracion")

        # Manejar la eliminación de un auto
        elif operation == "eliminar_auto":
            try:
                patente = request.POST.get("patente")
                auto = get_object_or_404(Auto, patente=patente)
                auto.delete()
                messages.success(request, f"Auto {patente} eliminado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar el auto: {str(e)}")
            return redirect("administracion")

        # Lógica original para asignar pedidos
        elif operation == "asignar_pedido":
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

                cliente = pedido.id_cliente
                usuario = User.objects.get(email=cliente.correo)

                Notificacion.objects.create(
                    usuario=usuario,
                    mensaje="Tu viaje ha sido asignado, el chofer está en camino."
                )

                messages.success(request, "Pedido asignado correctamente.")
                return redirect("administracion")

            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        # Crear chofer
        elif operation == "crear_chofer":
            try:
                nombre = request.POST.get("nombre")
                apellido = request.POST.get("apellido")
                nro_tel = request.POST.get("nro_tel")
                licencia = request.FILES.get("licencia")
                foto = request.FILES.get("foto")  # Nuevo campo

                Chofer.objects.create(
                    nombre=nombre,
                    apellido=apellido,
                    nro_tel=nro_tel,
                    licencia=licencia,
                    foto=foto
                )
                messages.success(request, "Chofer creado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al crear el chofer: {str(e)}")
            return redirect("administracion")

        # Editar chofer
        elif operation == "editar_chofer":
            try:
                id_chofer = request.POST.get("id_chofer")
                chofer = get_object_or_404(Chofer, id_chofer=id_chofer)

                chofer.nombre = request.POST.get("nombre", chofer.nombre)
                chofer.apellido = request.POST.get("apellido", chofer.apellido)
                chofer.nro_tel = request.POST.get("nro_tel", chofer.nro_tel)

                if "cambiar_licencia" in request.POST and "licencia" in request.FILES:
                    chofer.licencia = request.FILES.get("licencia")

                if "cambiar_foto" in request.POST and "foto" in request.FILES:
                    chofer.foto = request.FILES.get("foto")

                chofer.save()
                messages.success(request, f"Chofer {chofer.nombre} actualizado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al actualizar el chofer: {str(e)}")
            return redirect("administracion")

                # Eliminar chofer
        elif operation == "eliminar_chofer":
            try:
                id_chofer = request.POST.get("id_chofer")
                chofer = get_object_or_404(Chofer, id_chofer=id_chofer)
                chofer.delete()
                messages.success(request, f"Chofer eliminado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar el chofer: {str(e)}")
            return redirect("administracion")

        # Asignar auto a chofer
        elif operation == "asignar_auto":
            try:
                patente = request.POST.get("patente")
                id_chofer = request.POST.get("id_chofer")
                turno = request.POST.get("turno")

                if not patente or not id_chofer:
                    return JsonResponse({"status": "error", "message": "Datos incompletos para la asignación."}, status=400)

                auto = get_object_or_404(Auto, patente=patente)
                chofer = get_object_or_404(Chofer, id_chofer=id_chofer)

                ChoferAuto.objects.create(
                    patente=auto,
                    id_chofer=chofer,
                    turno=turno,
                    disponibilidad=True
                )
                messages.success(request, f"Auto {auto.patente} asignado a {chofer.nombre} {chofer.apellido} correctamente.")
            except Exception as e:
                messages.error(request, f"Error al asignar el auto: {str(e)}")
            return redirect("administracion")

        # Eliminar asignación de auto
        elif operation == "eliminar_asignacion_auto":
            try:
                patente = request.POST.get("patente")
                id_chofer = request.POST.get("id_chofer")

                if not patente or not id_chofer:
                    return JsonResponse({"status": "error", "message": "Datos incompletos para la eliminación de asignación."}, status=400)

                chofer_auto = get_object_or_404(ChoferAuto, patente=patente, id_chofer=id_chofer)
                chofer_auto.delete()
                messages.success(request, f"Asignación del auto {patente} para el chofer con ID {id_chofer} eliminada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar la asignación: {str(e)}")
            return redirect("administracion")
        
        
        elif operation == "eliminar_viaje":
            try:
                id_viaje = request.POST.get("id_viaje")
                viaje = get_object_or_404(Viaje, id_viaje=id_viaje)
                viaje.delete()
                messages.success(request, f"Viaje con ID {id_viaje} eliminado correctamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar el viaje: {str(e)}")
            return redirect("administracion")
            
        # Si la operación no es válida
        else:
            return JsonResponse({"status": "error", "message": "Operación desconocida."}, status=400)    






@base_required
def base_pedidos(request):
    # Recuperar autos registrados
    autos = Auto.objects.all()

    # Pasar los autos al template
    return render(request, 'base_pedidos.html', {'autos': autos})



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
        
def remiserias(request):
    # Obtener todas las remiserías desde la base de datos
    remiseria = Remiseria.objects.all()
    
    # Pasar las remiserías al template
    return render(request, 'remiseria.html', {'remiserias': remiseria})

def viaje(request):
    try:
        # Obtener el cliente actual
        cliente = Cliente.objects.get(correo=request.user.email)

        # Buscar el viaje asignado
        viaje = Viaje.objects.filter(id_cliente=cliente.id_cliente, estado="En viaje").first()

        if not viaje:
            return render(request, 'viaje.html', {'error': "No tienes un viaje en progreso."})

        # Obtener la información del chofer y del auto
        chofer_auto = ChoferAuto.objects.get(patente=viaje.patente)
        chofer = Chofer.objects.get(id_chofer=chofer_auto.id_chofer.id_chofer)
        auto = Auto.objects.get(patente=viaje.patente)

        # Enviar los datos al template
        return render(request, 'viaje.html', {
            'viaje': viaje,
            'chofer': chofer,
            'auto': auto
        })

    except Auto.DoesNotExist:
        return render(request, 'viaje.html', {
            'error': f"El auto asociado al viaje con la patente '{viaje.patente}' no existe."
        })
    except ChoferAuto.DoesNotExist:
        return render(request, 'viaje.html', {'error': "No se encontró información del chofer para este auto."})
    except Chofer.DoesNotExist:
        return render(request, 'viaje.html', {'error': "No se encontró información del chofer."})
    except Exception as e:
        return render(request, 'viaje.html', {'error': str(e)})
    
@login_required  
def obtener_api_key(request):
    return JsonResponse({"api_key": settings.ORS_API_KEY})


#AUTOSSSSSSSS
# Listar autos (Read)

def listar_autos(request):
    autos = Auto.objects.all()
    remiserias = Remiseria.objects.all()  # Obtener todas las remiserías
    return render(request, 'autos/listar_autos.html', {
        'autos': autos,
        'remiserias': remiserias
    })



# Crear un nuevo auto (Create)
from django.contrib import messages

def crear_auto(request):
    if request.method == 'POST':
        try:
            patente = request.POST['patente']
            tipo = request.POST['tipo']
            anio_modelo = request.POST['anio_modelo']
            propietario = request.POST['propietario']
            vtv = request.POST['vtv']
            venc_patente = request.POST['venc_patente']
            id_remiseria = request.POST['id_remiseria']
            foto = request.FILES.get('foto', None)

            Auto.objects.create(
                patente=patente,
                tipo=tipo,
                anio_modelo=anio_modelo,
                propietario=propietario,
                vtv=vtv,
                venc_patente=venc_patente,
                id_remiseria=id_remiseria,
                foto=foto
            )
            messages.success(request, "Auto agregado correctamente.")
        except Exception as e:
            messages.error(request, f"No se pudo agregar el auto: {str(e)}")

        # Volvemos a cargar los datos necesarios para base_pedidos
        pedidos_pendientes = PedidosCliente.objects.filter(estado_pedido="Pendiente")
        choferes_disponibles = ChoferAuto.objects.filter(disponibilidad=True)
        viajes_en_viaje = Viaje.objects.filter(estado="En viaje")
        autos = Auto.objects.all()
        remiserias = Remiseria.objects.all()

        return render(request, "base_pedidos.html", {
            "pedidos": pedidos_pendientes,
            "choferes": choferes_disponibles,
            "viajes_en_viaje": viajes_en_viaje,
            "autos": autos,
            "remiserias": remiserias,
        })


def editar_auto(request, patente):
    auto = get_object_or_404(Auto, patente=patente)  # Obtiene el auto o lanza un 404 si no existe
    if request.method == 'POST':
        try:
            # Actualizar los datos enviados en el formulario
            auto.tipo = request.POST.get('tipo', auto.tipo)
            auto.anio_modelo = request.POST.get('anio_modelo', auto.anio_modelo)
            auto.propietario = request.POST.get('propietario', auto.propietario)
            auto.id_remiseria = request.POST.get('id_remiseria', auto.id_remiseria)

            # Solo actualizar la foto si el switch está activado
            if "cambiar_foto" in request.POST and "foto" in request.FILES:
                auto.foto = request.FILES["foto"]

            # Guardar los cambios
            auto.save()
            messages.success(request, f"Auto {auto.patente} actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar el auto: {str(e)}")
        
        # Redirigir a la página principal después de procesar
        return redirect('administracion')

    # Si no es un método POST, muestra un error o redirige
    messages.error(request, "Método no permitido para esta operación.")
    return redirect('administracion')

    

def eliminar_auto(request, patente):
    auto = get_object_or_404(Auto, patente=patente)  # Recupera el auto o lanza un 404
    if request.method == 'POST':
        try:
            auto.delete()  # Elimina el auto de la base de datos
            messages.success(request, f"Auto {patente} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el auto: {str(e)}")
        return redirect('administracion')

    # Si no es POST, redirige con un mensaje de error
    messages.error(request, "Método no permitido para esta operación.")
    return redirect('administracion')



@login_required
def crear_asignacion(request):
    if request.method == "POST":
        id_chofer = request.POST.get("id_chofer")
        patente = request.POST.get("patente")
        turno = request.POST.get("turno")
        disponibilidad = request.POST.get("disponibilidad") == "True"

        try:
            chofer = get_object_or_404(Chofer, id_chofer=id_chofer)
            auto = get_object_or_404(Auto, patente=patente)

            ChoferAuto.objects.create(
                id_chofer=chofer,
                patente=auto,
                turno=turno,
                disponibilidad=disponibilidad
            )
            messages.success(request, "Asignación creada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al crear la asignación: {str(e)}")

        return redirect("administracion")


@login_required
def eliminar_asignacion(request, id_chofer, patente):
    try:
        asignacion = get_object_or_404(ChoferAuto, id_chofer=id_chofer, patente=patente)
        asignacion.delete()
        messages.success(request, "Asignación eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la asignación: {str(e)}")

    return redirect("administracion")
