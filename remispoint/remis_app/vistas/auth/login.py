from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from remis_app.models import Cliente

def vista_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        fcm_token = request.POST.get('fcm_token')

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            try:
                cliente = Cliente.objects.get(correo=user.email)
                cliente.fcm_token = fcm_token
                cliente.save()
            except Cliente.DoesNotExist:
                pass

            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'base/login.html', {'form': form})


from django.contrib.auth import login

def custom_login(request, user):
    login(request, user)