from django.shortcuts import render, redirect # type: ignore
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from remis_app.models import *
from django.contrib import messages

def crear_auto(request):
    if request.method == 'POST':
        try:
            patente = request.POST['patente']
            tipo = request.POST['tipo']
            anio_modelo = request.POST['anio_modelo']
            propietario = request.POST['propietario']
            vtv = request.POST['vtv']
            venc_patente = request.POST['venc_patente']
            id_remiseria = request.POST['id_remiseria']
            foto = request.FILES.get('foto', None)

            Auto.objects.create(
                patente=patente,
                tipo=tipo,
                anio_modelo=anio_modelo,
                propietario=propietario,
                vtv=vtv,
                venc_patente=venc_patente,
                id_remiseria=id_remiseria,
                foto=foto
            )
            messages.success(request, "Auto agregado correctamente.")
        except Exception as e:
            messages.error(request, f"No se pudo agregar el auto: {str(e)}")

        # Volvemos a cargar los datos necesarios para base_pedidos
        pedidos_pendientes = PedidosCliente.objects.filter(estado_pedido="Pendiente")
        choferes_disponibles = ChoferAuto.objects.filter(disponibilidad=True)
        viajes_en_viaje = Viaje.objects.filter(estado="Asignado")
        autos = Auto.objects.all()
        remiserias = Remiseria.objects.all()

        return render(request, "administracion_base/base_pedidos.html", {
            "pedidos": pedidos_pendientes,
            "choferes": choferes_disponibles,
            "viajes_en_viaje": viajes_en_viaje,
            "autos": autos,
            "remiserias": remiserias,
        })


def editar_auto(request, patente):
    auto = get_object_or_404(Auto, patente=patente)  # Obtiene el auto o lanza un 404 si no existe
    if request.method == 'POST':
        try:
            # Actualizar los datos enviados en el formulario
            auto.tipo = request.POST.get('tipo', auto.tipo)
            auto.anio_modelo = request.POST.get('anio_modelo', auto.anio_modelo)
            auto.propietario = request.POST.get('propietario', auto.propietario)
            auto.id_remiseria = request.POST.get('id_remiseria', auto.id_remiseria)

            # Solo actualizar la foto si el switch está activado
            if "cambiar_foto" in request.POST and "foto" in request.FILES:
                auto.foto = request.FILES["foto"]

            # Guardar los cambios
            auto.save()
            messages.success(request, f"Auto {auto.patente} actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar el auto: {str(e)}")
        
        # Redirigir a la página principal después de procesar
        return redirect('administracion')

    # Si no es un método POST, muestra un error o redirige
    messages.error(request, "Método no permitido para esta operación.")
    return redirect('administracion')

    

def eliminar_auto(request, patente):
    auto = get_object_or_404(Auto, patente=patente)  # Recupera el auto o lanza un 404
    if request.method == 'POST':
        try:
            auto.delete()  # Elimina el auto de la base de datos
            messages.success(request, f"Auto {patente} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar el auto: {str(e)}")
        return redirect('administracion')

    # Si no es POST, redirige con un mensaje de error
    messages.error(request, "Método no permitido para esta operación.")
    return redirect('administracion')


def listar_autos(request):
    autos = Auto.objects.all()
    remiserias = Remiseria.objects.all()  # Obtener todas las remiserías
    return render(request, 'administracion_base/autos/listar_autos.html', {
        'autos': autos,
        'remiserias': remiserias
    })