from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from remis_app.models import *
from django.contrib import messages

@login_required
def crear_asignacion(request):
    if request.method == "POST":
        id_chofer = request.POST.get("id_chofer")
        patente = request.POST.get("patente")
        turno = request.POST.get("turno")
        disponibilidad = request.POST.get("disponibilidad") == "True"

        try:
            chofer = get_object_or_404(Chofer, id_chofer=id_chofer)
            auto = get_object_or_404(Auto, patente=patente)

            ChoferAuto.objects.create(
                id_chofer=chofer,
                patente=auto,
                turno=turno,
                disponibilidad=disponibilidad
            )
            messages.success(request, "Asignación creada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al crear la asignación: {str(e)}")

        return redirect("administracion")


@login_required
def eliminar_asignacion(request, id_chofer, patente):
    try:
        asignacion = get_object_or_404(ChoferAuto, id_chofer=id_chofer, patente=patente)
        asignacion.delete()
        messages.success(request, "Asignación eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la asignación: {str(e)}")

    return redirect("administracion")