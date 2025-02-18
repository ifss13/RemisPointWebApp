from remis_app.models import Cliente, Viaje, PedidosCliente
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required


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