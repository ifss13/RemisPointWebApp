from django.http import JsonResponse
from remis_app.models import Precio


def obtener_id_precio(request):
    """Recibe la distancia en km y devuelve el id_precio correspondiente en la tabla Precio."""
    distancia_km = request.GET.get('distancia', None)

    if distancia_km is None:
        return JsonResponse({'error': 'Distancia no proporcionada'}, status=400)

    try:
        # Redondear la distancia a 1 decimal
        distancia_redondeada = round(float(distancia_km), 1)

        # Convertir la distancia a string para compararla con "descripcion" en la tabla Precio
        distancia_str = str(distancia_redondeada)

        # Buscar el id_precio basado en la descripción de la distancia
        precio = Precio.objects.filter(descripcion=distancia_str).first()

        if not precio:
            return JsonResponse({'error': 'No se encontró un id_precio para esta distancia'}, status=404)

        return JsonResponse({'id_precio': precio.id_precio})

    except ValueError:
        return JsonResponse({'error': 'Distancia inválida'}, status=400)