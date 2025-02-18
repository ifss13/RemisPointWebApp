from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from ...models import Cliente

@login_required
def cambiar_contrasena(request):
    """
    Vista para cambiar la contraseña del usuario en ambas tablas.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Cambiar la contraseña en auth_user
            user = form.save()
            update_session_auth_hash(request, user)  # Mantener la sesión activa tras cambiar la contraseña

            # Cambiar la contraseña en la tabla Clientes
            cliente = Cliente.objects.get(correo=request.user.email)  # Buscar al cliente por el correo del usuario
            cliente.password = user.password  # Actualizar el campo 'password' en la tabla Clientes
            cliente.save()

            # Responder con éxito en formato JSON
            return JsonResponse({
                'status': 'success',
                'message': 'Tu contraseña ha sido cambiada con éxito.'
            })
        else:
            # Si hay errores de validación, devolverlos en formato JSON
            return JsonResponse({
                'status': 'error',
                'message': 'Por favor corrige los errores a continuación.',
                'errors': form.errors
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Método no permitido.'
        })
