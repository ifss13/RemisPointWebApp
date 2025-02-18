from remis_app.models import Chofer, Auto, Viaje, Cliente
from django.shortcuts import get_object_or_404
from django.shortcuts import render

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