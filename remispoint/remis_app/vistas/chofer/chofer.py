from django.shortcuts import render
from remis_app.decorador import chofer_required
from remis_app.models import Cliente, Chofer, Viaje

from remis_app.decorador import chofer_required
from remis_app.models import Cliente, Chofer, Viaje

@chofer_required
def panel_chofer(request):
    try:
        # Obtener el cliente del chofer logueado
        cliente = Cliente.objects.filter(correo=request.user.email).first()
        if not cliente:
            return render(request, "chofer/panel_chofer.html", {"error": "Cliente no encontrado."})

        # Obtener la información del chofer
        chofer = Chofer.objects.filter(id_cliente=cliente).first()
        print(chofer)
        if not chofer:
            return render(request, "chofer/panel_chofer.html", {"error": "Chofer no encontrado."})


        # Obtener el viaje en curso (Asignado, En camino al cliente, En viaje)
        viaje = Viaje.objects.filter(id_chofer=chofer, estado__in=["Asignado", "En camino al cliente", "En viaje"]).first()

        if viaje:
            # Obtener el id_cliente del cliente relacionado con el viaje
            id_cliente = viaje.id_cliente

            # Obtener el fcm_token del cliente
            cliente_viaje = id_cliente  # ya tenés el objeto Cliente
            fcm_token = cliente_viaje.fcm_token if cliente_viaje else None
            print(fcm_token)

            # Puedes hacer algo con el fcm_token aquí (enviar notificación, etc.)
            print(f"fcm_token del cliente: {fcm_token}")
        else:
            fcm_token = None

        return render(request, "chofer/panel_chofer.html", {
            "chofer": chofer,
            "viaje": viaje,  # Será None si no hay un viaje en curso
            "fcm_token": fcm_token,  # Pasar el fcm_token a la plantilla si lo necesitas
        })

    except Exception as e:
        return render(request, "chofer/panel_chofer.html", {"error": str(e)})
