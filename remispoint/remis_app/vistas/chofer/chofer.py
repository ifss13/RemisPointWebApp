from django.shortcuts import render
from remis_app.decorador import chofer_required
from remis_app.models import Cliente, Chofer, Viaje

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