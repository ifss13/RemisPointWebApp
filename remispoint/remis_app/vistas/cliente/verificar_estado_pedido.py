from remis_app.models import PedidosCliente
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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
        
        # ✅ Por si hay otros estados no considerados
        return JsonResponse({'estado_pedido': pedido.estado_pedido})

    except PedidosCliente.DoesNotExist:
        return JsonResponse({'estado_pedido': 'Error', 'message': 'Pedido no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({'estado_pedido': 'Error', 'message': str(e)}, status=500)
