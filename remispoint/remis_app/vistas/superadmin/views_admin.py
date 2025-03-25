from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from remis_app.models import Cliente
from remis_app.forms import ClienteForm
from django.views.decorators.csrf import csrf_exempt

def cargar_form_cliente(request, cliente_id=None):
    try:
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            form = ClienteForm(instance=cliente)
        else:
            form = ClienteForm()

        contexto = {'form': form}
        html_form = render_to_string('admin_super/componentes/form_cliente.html', contexto, request=request)
        return JsonResponse({'html_form': html_form})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt 
def guardar_cliente(request, cliente_id=None):
    if request.method == 'POST':
        if cliente_id:
            cliente = Cliente.objects.get(pk=cliente_id)
            form = ClienteForm(request.POST, instance=cliente)
        else:
            form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('admin_super/componentes/form_cliente.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'html_form': html_form})

@csrf_exempt  # O quitá esto si ya estás manejando CSRF desde el template
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    cliente.delete()
    return JsonResponse({'success': True})


from remis_app.models import Chofer
from remis_app.forms import ChoferFormAdmin

def cargar_form_chofer(request, chofer_id=None):
    if chofer_id:
        chofer = get_object_or_404(Chofer, pk=chofer_id)
        form = ChoferFormAdmin(instance=chofer)
    else:
        form = ChoferFormAdmin()

    contexto = {'form': form}
    html_form = render_to_string('admin_super/componentes/form_chofer.html', contexto, request=request)
    return JsonResponse({'html_form': html_form})

@csrf_exempt
def guardar_chofer(request, chofer_id=None):
    if request.method == 'POST':
        if chofer_id:
            chofer = get_object_or_404(Chofer, pk=chofer_id)
            form = ChoferFormAdmin(request.POST, request.FILES, instance=chofer)
        else:
            form = ChoferFormAdmin(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('admin_super/componentes/form_chofer.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'html_form': html_form})

@csrf_exempt
def eliminar_chofer(request, chofer_id):
    chofer = get_object_or_404(Chofer, pk=chofer_id)
    chofer.delete()
    return JsonResponse({'success': True})


from remis_app.models import Viaje
from remis_app.forms import ViajeForm

def cargar_form_viaje(request, viaje_id=None):
    if viaje_id:
        viaje = get_object_or_404(Viaje, pk=viaje_id)
        form = ViajeForm(instance=viaje)
    else:
        form = ViajeForm()

    contexto = {'form': form}
    html_form = render_to_string('admin_super/componentes/form_viaje.html', contexto, request=request)
    return JsonResponse({'html_form': html_form})

@csrf_exempt
def guardar_viaje(request, viaje_id=None):
    if request.method == 'POST':
        if viaje_id:
            viaje = get_object_or_404(Viaje, pk=viaje_id)
            form = ViajeForm(request.POST, instance=viaje)
        else:
            form = ViajeForm(request.POST)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('admin_super/componentes/form_viaje.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'html_form': html_form})

@csrf_exempt
def eliminar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    viaje.delete()
    return JsonResponse({'success': True})


from remis_app.models import Remiseria
from remis_app.forms import RemiseriaForm

def cargar_form_remiseria(request, remiseria_id=None):
    if remiseria_id:
        remiseria = get_object_or_404(Remiseria, pk=remiseria_id)
        form = RemiseriaForm(instance=remiseria)
    else:
        form = RemiseriaForm()

    contexto = {'form': form}
    html_form = render_to_string('admin_super/componentes/form_remiseria.html', contexto, request=request)
    return JsonResponse({'html_form': html_form})

@csrf_exempt
def guardar_remiseria(request, remiseria_id=None):
    if request.method == 'POST':
        if remiseria_id:
            remiseria = get_object_or_404(Remiseria, pk=remiseria_id)
            form = RemiseriaForm(request.POST, request.FILES, instance=remiseria)
        else:
            form = RemiseriaForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('admin_super/componentes/form_remiseria.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'html_form': html_form})

@csrf_exempt
def eliminar_remiseria(request, remiseria_id):
    remiseria = get_object_or_404(Remiseria, pk=remiseria_id)
    remiseria.delete()
    return JsonResponse({'success': True})


from remis_app.models import Localidad
from remis_app.forms import LocalidadForm

def cargar_form_localidad(request, localidad_id=None):
    if localidad_id:
        localidad = get_object_or_404(Localidad, pk=localidad_id)
        form = LocalidadForm(instance=localidad)
    else:
        form = LocalidadForm()

    contexto = {'form': form}
    html_form = render_to_string('admin_super/componentes/form_localidad.html', contexto, request=request)
    return JsonResponse({'html_form': html_form})

@csrf_exempt
def guardar_localidad(request, localidad_id=None):
    if request.method == 'POST':
        if localidad_id:
            localidad = get_object_or_404(Localidad, pk=localidad_id)
            form = LocalidadForm(request.POST, instance=localidad)
        else:
            form = LocalidadForm(request.POST)

        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            html_form = render_to_string('admin_super/componentes/form_localidad.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'html_form': html_form})

@csrf_exempt
def eliminar_localidad(request, localidad_id):
    localidad = get_object_or_404(Localidad, pk=localidad_id)
    localidad.delete()
    return JsonResponse({'success': True})
