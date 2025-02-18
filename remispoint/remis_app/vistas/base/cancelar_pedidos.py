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