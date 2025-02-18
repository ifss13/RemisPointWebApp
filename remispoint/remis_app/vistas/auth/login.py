from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirige al usuario si ya está autenticado

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirige a la página de inicio después de iniciar sesión
        else:
            # Si el formulario no es válido, se renderiza nuevamente el login
            return render(request, 'base/login.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {'form': form})
