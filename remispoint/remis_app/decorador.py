from django.shortcuts import redirect
from functools import wraps
from remis_app.models import Cliente

def base_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Obtener el cliente relacionado
            try:
                cliente = Cliente.objects.get(correo=request.user.email)
                if cliente.tipo_cuenta == Cliente.BASE:  # Verificar si es "BASE"
                    return view_func(request, *args, **kwargs)
            except Cliente.DoesNotExist:
                pass

        # Redirigir si no tiene permiso
        return redirect('no_autorizado')  # Redirige a una página de error o inicio

    return _wrapped_view
