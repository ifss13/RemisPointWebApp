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
from remis_app.models import PedidosCliente, ChoferAuto, Cliente, Viaje, Chofer, Auto, Notificacion, Remiseria, TipoPago, Precio
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from remis_app.decorador import base_required, chofer_required
from django.views.decorators.csrf import csrf_exempt
from .forms import AutoForm
import urllib.parse
from django.utils.timezone import now

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
            return render(request, 'base/registro.html', {'error': "Correo no válido", 'localidades': Localidad.objects.all()})

        # Verificación de contraseñas
        if password != password2:
            return render(request, 'base/registro.html', {'error': "Las contraseñas no coinciden", 'localidades': Localidad.objects.all()})

        # Verificación de si el correo o el username ya existen
        if User.objects.filter(email=correo).exists():
            return render(request, 'base/registro.html', {'error': "Este correo ya está registrado", 'localidades': Localidad.objects.all()})
        if User.objects.filter(username=username).exists():
            return render(request, 'base/registro.html', {'error': "El nombre de usuario ya está registrado", 'localidades': Localidad.objects.all()})

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
            return render(request, 'base/registro.html', {'error': "Hubo un error al guardar los datos. Intenta nuevamente.", 'localidades': Localidad.objects.all()})

    # Si es GET, muestra el formulario de registro
    localidades = Localidad.objects.all()
    return render(request, 'base/registro.html', {'localidades': localidades})




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
            return render(request, 'base/login.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {'form': form})


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
            id_precio = data.get("id_precio")  # ✅ Nuevo campo para el precio
            cod_tipo_pago = data.get("cod_tipo_pago")  # ✅ Nuevo campo para el tipo de pago

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

            # Validar que id_precio y cod_tipo_pago estén presentes
            if not id_precio or not cod_tipo_pago:
                return JsonResponse({"status": "error", "message": "Debe seleccionarse un precio y un método de pago."}, status=400)

            # Obtener el cliente relacionado con el usuario actual
            cliente = get_object_or_404(Cliente, correo=request.user.email)

            # Obtener la instancia de Remiseria usando el id
            remiseria = get_object_or_404(Remiseria, id_remiseria=remiseria_id)

            # Obtener la instancia de Precio
            precio = get_object_or_404(Precio, id_precio=id_precio)  # ✅ Obtener la instancia del precio

            # Obtener la instancia de Tipo de Pago
            tipo_pago = get_object_or_404(TipoPago, cod_tipo_pago=cod_tipo_pago)  # ✅ Obtener la instancia del tipo de pago

            # Crear el registro en la tabla PedidoCliente
            pedido = PedidosCliente.objects.create(
                id_cliente=cliente,
                dir_salida=dir_salida,
                dir_destino=dir_destino,
                estado_pedido="Pendiente",
                id_remiseria=remiseria,  # Aquí asignas la instancia de Remiseria
                id_precio=precio,  # ✅ Guardamos el id_precio obtenido
                cod_tipo_pago=tipo_pago  # ✅ Guardamos el tipo de pago seleccionado
            )

            # Devolver la URL a la que se debe redirigir el cliente
            return JsonResponse({"status": "success", "redirect_url": f"/esperando_chofer/{pedido.id_pedido}/"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    elif request.method == "GET":
        remiseria_id = request.GET.get('remiseria_id')  # Capturamos el remiseria_id de la URL
        tipos_pago = TipoPago.objects.all()  # ✅ Obtener todos los métodos de pago disponibles

        return render(request, "clientes/pedidos.html", {'remiseria_id': remiseria_id, 'tipos_pago': tipos_pago})

    return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)





@login_required
def esperando_chofer(request, pedido_id):
    try:
        pedido = get_object_or_404(PedidosCliente, id_pedido=pedido_id)
        viaje = Viaje.objects.filter(id_cliente=pedido.id_cliente, estado="Asignado").first()
        
        # Si el viaje no ha sido asignado, mostramos el spinner de "Esperando asignación"
        if not viaje:
            return render(request, 'clientes/esperando_chofer.html', {
                'pedido_id': pedido_id,
                'viaje_asignado': False
            })

        # ✅ Usamos directamente el chofer del viaje
        chofer = viaje.id_chofer
        auto = viaje.patente  # `patente` en `Viaje` ya almacena la referencia del auto

        return render(request, 'clientes/esperando_chofer.html', {
            'pedido_id': pedido_id,
            'chofer': chofer,
            'auto': auto,
            'viaje_asignado': True,  # Solo mostramos la info cuando el viaje ya está asignado
        })
    except Exception as e:
        return render(request, 'clientes/esperando_chofer.html', {
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
        
        elif pedido.estado_pedido == "Cancelado por el Cliente":
            return JsonResponse({'estado_pedido': 'Cancelado por el Cliente'})
        
        elif pedido.estado_pedido == "Cancelado por la Base":
            return JsonResponse({'estado_pedido': 'Cancelado por la Base'})

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
        viajes_en_viaje = Viaje.objects.filter(estado="Asignado")
        autos = Auto.objects.all()
        remiserias = Remiseria.objects.all()
        choferes = Chofer.objects.all()
        asignaciones = ChoferAuto.objects.select_related('patente', 'id_chofer')  # Datos de la tabla puente
        viajes_registrados = Viaje.objects.all()
        tipopago = TipoPago.objects.all()

        return render(request, "administracion_base/base_pedidos.html", {
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

        elif operation == "asignar_pedido":
            try:
                id_pedido = request.POST.get("id_pedido")
                id_chofer = request.POST.get("id_chofer")

                if not id_pedido or not id_chofer:
                    return JsonResponse({"status": "error", "message": "Datos incompletos."}, status=400)

                id_pedido = int(id_pedido)
                id_chofer = int(id_chofer)

                pedido = get_object_or_404(PedidosCliente, id_pedido=id_pedido)

                # Obtener el registro correcto de ChoferAuto para este chofer
                chofer_auto = ChoferAuto.objects.filter(id_chofer=id_chofer, disponibilidad=True).first()
                if not chofer_auto:
                    return JsonResponse({"status": "error", "message": "No se encontró un auto disponible para este chofer."}, status=400)

                # Obtener el chofer relacionado
                chofer = get_object_or_404(Chofer, id_chofer=chofer_auto.id_chofer.id_chofer)

                # ✅ Obtener el precio y el tipo de pago desde el pedido
                id_precio = pedido.id_precio.id_precio  # Obtener el id_precio del pedido
                cod_tipo_pago = pedido.cod_tipo_pago.cod_tipo_pago  # Obtener el tipo de pago del pedido

                # Crear el viaje con el chofer correcto y su auto asignado
                viaje = Viaje.objects.create(
                    id_cliente=pedido.id_cliente,
                    id_chofer=chofer,  # 🔹 Se usa el chofer correcto desde ChoferAuto
                    dir_salida=pedido.dir_salida,
                    dir_destino=pedido.dir_destino,
                    hora=timezone.now().time(),
                    fecha=timezone.now().date(),
                    id_precio=get_object_or_404(Precio, id_precio=id_precio),  # ✅ Se obtiene el precio del pedido
                    cod_tipo_pago=get_object_or_404(TipoPago, cod_tipo_pago=cod_tipo_pago),  # ✅ Se obtiene el tipo de pago del pedido
                    id_remiseria=1,
                    inicio=timezone.now().time(),
                    fin=timezone.now().time(),
                    patente=chofer_auto.patente,  # 🔹 Se usa la patente del auto asignado
                    estado="Asignado"
                )

                # Actualizar estado del pedido y la disponibilidad del chofer
                pedido.estado_pedido = "Asignado"
                pedido.save()
                chofer_auto.disponibilidad = False
                chofer_auto.save()

                # Enviar notificación al cliente
                # cliente = pedido.id_cliente
                # usuario = User.objects.get(email=cliente.correo)

                # Notificacion.objects.create(
                    # usuario=usuario,
                    # mensaje="Tu viaje ha sido asignado, el chofer está en camino."
                #)

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
    return render(request, 'administracion_base/base_pedidos.html', {'autos': autos})



def finalizar_viaje(request, id_viaje):
    try:
        # Obtener el viaje a través del ID
        viaje = get_object_or_404(Viaje, id_viaje=id_viaje)

        # Obtener el chofer y el auto relacionados con el viaje
        id_chofer = viaje.id_chofer.id_chofer  # 🔹 Obtenemos el chofer directamente desde Viaje
        auto = viaje.patente  # 🔹 Obtenemos la patente desde Viaje

        # Obtener el ChoferAuto correspondiente a este chofer y auto
        chofer_auto = get_object_or_404(ChoferAuto, patente=auto, id_chofer=id_chofer)

        # Cambiar el estado del viaje a 'Finalizado'
        viaje.estado = "Cancelado por la Base"
        viaje.save()

        # Cambiar la disponibilidad del chofer a True
        chofer_auto.disponibilidad = True
        chofer_auto.save()

        # Devolver una respuesta JSON exitosa
        return JsonResponse({"status": "success", "message": "Viaje cancelado correctamente."})

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
    return render(request, 'base/panel_cuenta.html', {
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
        
def remiserias(request):
    # Obtener todas las remiserías desde la base de datos
    remiseria = Remiseria.objects.all()
    
    # Pasar las remiserías al template
    return render(request, 'clientes/remiseria.html', {'remiserias': remiseria})

def viaje(request):
    try:
        # Obtener el cliente actual
        cliente = Cliente.objects.get(correo=request.user.email)

        # Buscar el viaje asignado
        viaje = Viaje.objects.filter(id_cliente=cliente.id_cliente, estado="Asignado").first()

        if not viaje:
            return render(request, 'clientes/viaje.html', {'error': "No tienes un viaje en progreso."})

        # Obtener la información del chofer y del auto
        chofer = get_object_or_404(Chofer, id_chofer=viaje.id_chofer.id_chofer)  # 🔹 Lo obtenemos directo de Viaje
        auto = get_object_or_404(Auto, patente=viaje.patente)  # 🔹 Auto directo de Viaje

        return render(request, 'clientes/viaje.html', {
            'viaje': viaje,
            'chofer': chofer,
            'auto': auto
        })

    except Auto.DoesNotExist:
        return render(request, 'clientes/viaje.html', {
            'error': f"El auto asociado al viaje con la patente '{viaje.patente}' no existe."
        })
    except Chofer.DoesNotExist:
        return render(request, 'clientes/viaje.html', {'error': "No se encontró información del chofer."})
    except Exception as e:
        return render(request, 'clientes/viaje.html', {'error': str(e)})

    
@login_required  
def obtener_api_key(request):
    return JsonResponse({"api_key": settings.ORS_API_KEY})


#AUTOSSSSSSSS
# Listar autos (Read)

def listar_autos(request):
    autos = Auto.objects.all()
    remiserias = Remiseria.objects.all()  # Obtener todas las remiserías
    return render(request, 'administracion_base/autos/listar_autos.html', {
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
        viajes_en_viaje = Viaje.objects.filter(estado="Asignado")
        autos = Auto.objects.all()
        remiserias = Remiseria.objects.all()

        return render(request, "administracion_base/base_pedidos.html", {
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

@chofer_required
def panel_chofer(request):
    try:
        cliente = Cliente.objects.filter(correo=request.user.email).first()
        if not cliente:
            return render(request, "chofer/panel_chofer.html", {"error": "Cliente no encontrado."})

        chofer = Chofer.objects.filter(id_cliente=cliente).first()
        if not chofer:
            return render(request, "chofer/panel_chofer.html", {"error": "Chofer no encontrado."})

        # Obtener el viaje en curso, no solo asignado sino también en camino o en viaje
        viaje = Viaje.objects.filter(id_chofer=chofer, estado__in=["Asignado", "En camino al cliente", "En viaje"]).first()

        return render(request, "chofer/panel_chofer.html", {
            "chofer": chofer,
            "viaje": viaje  # Será None si no hay un viaje en curso
        })

    except Exception as e:
        return render(request, "chofer/panel_chofer.html", {"error": str(e)})



@csrf_exempt
def actualizar_estado_chofer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            disponible = data.get("disponible", False)

            # Obtener el cliente basado en el correo del usuario autenticado
            cliente = Cliente.objects.filter(correo=request.user.email).first()
            if not cliente:
                return JsonResponse({"status": "error", "message": "Cliente no encontrado."})

            # Obtener el chofer relacionado con el cliente
            chofer = Chofer.objects.filter(id_cliente=cliente).first()
            if not chofer:
                return JsonResponse({"status": "error", "message": "Chofer no encontrado."})

            # Obtener el ChoferAuto relacionado con el chofer
            chofer_auto = ChoferAuto.objects.filter(id_chofer=chofer).first()
            if not chofer_auto:
                return JsonResponse({"status": "error", "message": "No se encontró un registro en ChoferAuto para este chofer."})

            # Actualizar disponibilidad
            chofer_auto.disponibilidad = disponible
            chofer_auto.save()

            return JsonResponse({"status": "success", "message": "Estado actualizado correctamente"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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


from django.views.decorators.csrf import csrf_exempt
import json

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

            
            # ✅ Actualizar la hora de inicio cuando el viaje cambia a "En viaje"
            if nuevo_estado == "En viaje":
                viaje.inicio = now().time()

            # ✅ Actualizar la hora de finalización cuando el viaje cambia a "Finalizado"
            if nuevo_estado == "Finalizado":
                viaje.fin = now().time()

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

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from remis_app.models import PedidosCliente
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def cancelar_pedido_base(request, pedido_id):
    if request.method == "POST":
        try:
            pedido = get_object_or_404(PedidosCliente, id_pedido=pedido_id)

            if pedido.estado_pedido == "Pendiente":
                pedido.estado_pedido = "Cancelado por la Base"
                pedido.save()
                return JsonResponse({"success": True, "estado_pedido": "Cancelado por la Base"})
            else:
                return JsonResponse({"success": False, "error": "No se puede cancelar un pedido en este estado."})

        except PedidosCliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Pedido no encontrado."}, status=404)
        
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)


import urllib.parse
from django.shortcuts import redirect
from django.conf import settings

def conectar_mercadopago(request):
    """Redirige al usuario a la autorización de Mercado Pago SIN PKCE"""
    user = request.user
    if not user.is_authenticated:
        return redirect('login')

    auth_url = (
        f"https://auth.mercadopago.com/authorization"
        f"?response_type=code"
        f"&client_id={settings.MP_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(settings.MP_REDIRECT_URI)}"
        f"&scope=offline_access%20read"
    )

    return redirect(auth_url)


import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from remis_app.models import Chofer, Cliente
from django.conf import settings

@login_required
def mercadopago_callback(request):
    """Captura el código de autorización, obtiene el user_id del chofer y lo guarda"""
    if 'code' not in request.GET:
        return JsonResponse({'error': 'No authorization code provided'}, status=400)

    auth_code = request.GET['code']

    # URL de Mercado Pago para obtener el mp_user_id
    token_url = "https://api.mercadopago.com/oauth/token"

    data = {
        'client_id': settings.MP_CLIENT_ID,
        'client_secret': settings.MP_CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.MP_REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code != 200:
        print("ERROR Mercado Pago:", response.json())  # ✅ Ver qué está fallando exactamente
        return JsonResponse({
            'error': 'Failed to obtain access token',
            'status_code': response.status_code,
            'response': response.json()
        }, status=400)

    token_data = response.json()
    mp_user_id = token_data.get('user_id')  # ✅ Obtenemos el mp_user_id del chofer

    # 📌 PASO 1: Buscar el cliente usando el email del usuario autenticado
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=400)

    # 📌 PASO 2: Buscar el chofer asociado al cliente
    try:
        chofer = Chofer.objects.get(id_cliente=cliente.id_cliente)
    except Chofer.DoesNotExist:
        return JsonResponse({'error': 'Chofer no encontrado'}, status=400)

    # 📌 PASO 3: Asignar el nuevo mp_user_id y guardar
    chofer.mp_user_id = mp_user_id
    chofer.save()

    return redirect('chofer')  # Redirigir al panel del chofer

from django.http import JsonResponse
from remis_app.models import Precio

def obtener_precio(request):
    """Recibe la distancia, la redondea y busca el precio en la base de datos"""
    distancia_km = request.GET.get('distancia', None)

    if distancia_km is None:
        return JsonResponse({'error': 'Distancia no proporcionada'}, status=400)

    try:
        # Redondear la distancia a 1 decimal
        distancia_redondeada = round(float(distancia_km), 1)

        # Buscar el precio en la base de datos según la descripción (redondeo a string)
        precio = Precio.objects.filter(descripcion=str(distancia_redondeada)).first()

        if not precio:
            return JsonResponse({'error': 'No se encontró un precio para esta distancia'}, status=404)

        return JsonResponse({'precio': precio.precio})

    except ValueError:
        return JsonResponse({'error': 'Distancia inválida'}, status=400)


def obtener_id_precio(request):
    """Recibe la distancia en km y devuelve el id_precio correspondiente en la tabla Precio."""
    distancia_km = request.GET.get('distancia', None)

    if distancia_km is None:
        return JsonResponse({'error': 'Distancia no proporcionada'}, status=400)

    try:
        # Redondear la distancia a 1 decimal
        distancia_redondeada = round(float(distancia_km), 1)

        # Convertir la distancia a string para compararla con "descripcion" en la tabla Precio
        distancia_str = str(distancia_redondeada)

        # Buscar el id_precio basado en la descripción de la distancia
        precio = Precio.objects.filter(descripcion=distancia_str).first()

        if not precio:
            return JsonResponse({'error': 'No se encontró un id_precio para esta distancia'}, status=404)

        return JsonResponse({'id_precio': precio.id_precio})

    except ValueError:
        return JsonResponse({'error': 'Distancia inválida'}, status=400)


@login_required
def verificar_estado_viaje(request, id_viaje):
    """Devuelve el estado actual del viaje para actualizar dinámicamente la interfaz del cliente."""
    viaje = get_object_or_404(Viaje, id_viaje=id_viaje)

    return JsonResponse({"estado": viaje.estado})

from django.shortcuts import render, get_object_or_404
from remis_app.models import Viaje

import mercadopago

import json
import mercadopago
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from remis_app.models import Viaje, Chofer

@login_required
def pagos(request, id_viaje):
    """Vista para mostrar el resumen del viaje y generar el pago si es con MercadoPago."""
    print(f"🔎 Buscando viaje con ID: {id_viaje}")
    viaje = get_object_or_404(Viaje, id_viaje=id_viaje)
    print(f"✅ Viaje encontrado: {viaje}")

    preference_id = None
    if viaje.cod_tipo_pago.cod_tipo_pago == 3:
        print("✅ El método de pago es MercadoPago.")
        chofer = get_object_or_404(Chofer, id_chofer=viaje.id_chofer.id_chofer)
        print(f"🔎 Buscando chofer con ID: {viaje.id_chofer.id_chofer}")

        if chofer.mp_user_id:
            print(f"✅ Chofer encontrado con MP_USER_ID: {chofer.mp_user_id}")

            try:
                sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
                print(f"🔎 Usando ACCESS_TOKEN: {settings.MP_ACCESS_TOKEN}")

                preference_data = {
                    "items": [
                        {
                            "title": "Pago del viaje",
                            "quantity": 1,
                            "currency_id": "ARS",
                            "unit_price": float(viaje.id_precio.precio)
                        }
                    ],
                    "payer": {
                        "email": request.user.email
                    },
                    "collector_id": int(chofer.mp_user_id) if chofer.mp_user_id else None,
                    "external_reference": str(viaje.id_viaje),
                    "notification_url": f"{settings.SITE_URL}/mp_webhook/",
                    "auto_return": "approved",
                    "back_urls": {
                        "success": f"{settings.SITE_URL}/pagos_exitoso/{viaje.id_viaje}/",
                        "failure": f"{settings.SITE_URL}/pagos_fallido/{viaje.id_viaje}/",
                        "pending": f"{settings.SITE_URL}/pagos_pendiente/{viaje.id_viaje}/"
                    }
                }

                print("🔎 Datos enviados a MercadoPago:", json.dumps(preference_data, indent=4))

                preference_response = sdk.preference().create(preference_data)
                print("🔎 Respuesta completa de MercadoPago:", preference_response)

                if "response" in preference_response and "id" in preference_response["response"]:
                    preference_id = preference_response["response"]["id"]
                    print(f"✅ Preference ID generado correctamente: {preference_id}")
                else:
                    print("🚨 Error: No se pudo obtener preference_id de MercadoPago.")
                    print(f"❌ Respuesta de MercadoPago: {preference_response}")

            except Exception as e:
                print(f"🚨 Error al generar la preferencia de pago: {str(e)}")

    return render(request, "clientes/pagos.html", {"viaje": viaje, "preference_id": preference_id})




@csrf_exempt
def mp_webhook(request):
    """Procesa las notificaciones de pago de MercadoPago."""
    try:
        data = json.loads(request.body)
        external_reference = data.get("external_reference")
        payment_status = data.get("status")

        if external_reference and payment_status:
            viaje = Viaje.objects.get(id_viaje=external_reference)
            if payment_status == "approved":
                viaje.estado = "Pago Confirmado"
                viaje.save(update_fields=["estado"])

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def pagos_exitoso(request, id_viaje):
    """Vista cuando el pago se completa con éxito."""
    return render(request, "clientes/pagos_exitoso.html", {"id_viaje": id_viaje})

@login_required
def pagos_fallido(request, id_viaje):
    """Vista cuando el pago falla."""
    return render(request, "clientes/pagos_fallido.html", {"id_viaje": id_viaje})

@login_required
def pagos_pendiente(request, id_viaje):
    """Vista cuando el pago queda pendiente."""
    return render(request, "clientes/pagos_pendiente.html", {"id_viaje": id_viaje})
