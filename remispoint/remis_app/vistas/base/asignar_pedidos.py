from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from remis_app.models import *
from django.conf import settings
from remis_app.models import PedidosCliente, ChoferAuto, Viaje, Chofer, Auto,  Remiseria, TipoPago, Precio
from django.shortcuts import get_object_or_404
from django.contrib import messages
from remis_app.decorador import base_required
from django.utils.timezone import now
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
                pedido.estado_pedido = "Esperando al chofer"
                pedido.save()
                chofer_auto.disponibilidad = False
                chofer_auto.save()

                # Obtener el fcm_token del chofer para enviar la notificación
                fcm_token = chofer.id_cliente.fcm_token

                # Enviar la notificación al chofer
                mensaje = f"Se te ha asignado un nuevo viaje: {pedido.dir_salida} -> {pedido.dir_destino}"
                if fcm_token:
                    enviar_notificacion(fcm_token, mensaje)

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
        

import requests
def enviar_notificacion(player_id, mensaje):
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
    return response.json()

