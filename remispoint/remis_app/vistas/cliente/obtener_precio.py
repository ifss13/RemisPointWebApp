from django.http import JsonResponse
from remis_app.models import Precio

def obtener_precio(request):
    """Recibe la distancia, la redondea y busca el precio en la base de datos"""
    distancia_km = request.GET.get('distancia', None)

    if distancia_km is None:
        return JsonResponse({'error': 'Distancia no proporcionada'}, status=400)

    try:
        # Redondear la distancia a 1 decimal
        distancia_redondeada = round(float(distancia_km), 1)

        # Buscar el precio en la base de datos según la descripción (redondeo a string)
        precio = Precio.objects.filter(descripcion=str(distancia_redondeada)).first()

        if not precio:
            return JsonResponse({'error': 'No se encontró un precio para esta distancia'}, status=404)

        return JsonResponse({'precio': precio.precio})

    except ValueError:
        return JsonResponse({'error': 'Distancia inválida'}, status=400)