from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from remis_app.models import Viaje, PedidosCliente


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