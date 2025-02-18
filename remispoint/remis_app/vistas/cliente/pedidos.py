from remis_app.models import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json
from django.shortcuts import render

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