from remis_app.models import Chofer, Auto, Viaje, Cliente, Rating
from django.db.models import Avg
from django.shortcuts import get_object_or_404, render

def viaje(request):
    try:
        # Obtener el cliente actual
        cliente = Cliente.objects.get(correo=request.user.email)

        # Buscar el viaje asignado
        viaje = Viaje.objects.filter(
            id_cliente=cliente.id_cliente,
            estado__in=["Asignado", "En camino al cliente", "En viaje"]
        ).first()


        if not viaje:
            return render(request, 'clientes/viaje.html', {'error': "No tienes un viaje en progreso."})

        # Obtener la información del chofer y del auto
        chofer = get_object_or_404(Chofer, id_chofer=viaje.id_chofer.id_chofer)
        auto = get_object_or_404(Auto, patente=viaje.patente)

        # Calcular el promedio de ratings del chofer
        promedio_rating = Rating.objects.filter(id_chofer=chofer).aggregate(Avg('calificacion'))['calificacion__avg']

        return render(request, 'clientes/viaje.html', {
            'viaje': viaje,
            'chofer': chofer,
            'auto': auto,
            'promedio_rating': round(promedio_rating, 1) if promedio_rating else "Sin calificaciones"
        })

    except Auto.DoesNotExist:
        return render(request, 'clientes/viaje.html', {
            'error': f"El auto asociado al viaje con la patente '{viaje.patente}' no existe."
        })
    except Chofer.DoesNotExist:
        return render(request, 'clientes/viaje.html', {'error': "No se encontró información del chofer."})
    except Exception as e:
        return render(request, 'clientes/viaje.html', {'error': str(e)})
