from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from remis_app.models import Cliente  # Importa tu modelo de Clientes

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirige al usuario si ya está autenticado

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        fcm_token = request.POST.get('fcm_token')  # Obtiene el token desde el frontend

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Buscar al usuario en la tabla Clientes y actualizar su token
            try:
                cliente = Cliente.objects.get(correo=user.email)
                cliente.fcm_token = fcm_token  # Actualiza el token
                cliente.save()  # Guarda los cambios en la base de datos
            except Cliente.DoesNotExist:
                pass  # Si el usuario no está en Clientes, no hacemos nada

            return redirect('home')  # Redirige después del login exitoso

    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {'form': form})
