from django.shortcuts import render
from remis_app.models import Remiseria

def remiserias(request):
    # Obtener todas las remiserías desde la base de datos
    remiseria = Remiseria.objects.all()
    
    # Pasar las remiserías al template
    return render(request, 'clientes/remiseria.html', {'remiserias': remiseria})