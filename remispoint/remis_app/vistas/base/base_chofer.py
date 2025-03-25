# remis_app/vistas/choferes.py (o donde estés manejando esto)

from django.shortcuts import render, redirect
from remis_app.forms import ChoferForm
from remis_app.models import Chofer

def crear_chofer(request):
    remiseria_id = request.session.get('id_remiseria')
    if not remiseria_id:
        return render(request, 'error.html', {'mensaje': 'Código de remisería no encontrado o sesión expirada.'})

    if request.method == 'POST':
        form = ChoferForm(request.POST, request.FILES)
        if form.is_valid():
            chofer = form.save(commit=False)
            chofer.id_remiseria_id = remiseria_id  # Asociar automáticamente
            chofer.save()
            return redirect('listar_choferes')  # Cambiá esto al nombre de la vista/listado correspondiente
    else:
        form = ChoferForm()

    return render(request, 'administracion_base/choferes/crear_chofer.html', {'form': form})
