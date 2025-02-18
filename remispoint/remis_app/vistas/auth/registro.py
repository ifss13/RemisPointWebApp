from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from remis_app.models import Cliente, Localidad
from django.db import IntegrityError

def register(request):
    if request.method == "POST":
        # Obtener los datos del formulario
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        username = request.POST['username']
        telefono = request.POST['telefono']
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        password = request.POST['password']
        password2 = request.POST['password2']
        localidad = request.POST['localidad']

        # Verificación de formato de correo
        if not correo or '@' not in correo:
            return render(request, 'base/registro.html', {'error': "Correo no válido", 'localidades': Localidad.objects.all()})

        # Verificación de contraseñas
        if password != password2:
            return render(request, 'base/registro.html', {'error': "Las contraseñas no coinciden", 'localidades': Localidad.objects.all()})

        # Verificación de si el correo o el username ya existen
        if User.objects.filter(email=correo).exists():
            return render(request, 'base/registro.html', {'error': "Este correo ya está registrado", 'localidades': Localidad.objects.all()})
        if User.objects.filter(username=username).exists():
            return render(request, 'base/registro.html', {'error': "El nombre de usuario ya está registrado", 'localidades': Localidad.objects.all()})

        try:
            # Crear un nuevo usuario en Django (tabla auth_user)
            user = User.objects.create_user(
                username=username,
                password=password,
                email=correo,
                first_name=nombre,
                last_name=apellido
            )

            # Relacionar con la tabla de clientes
            localidad_obj = Localidad.objects.get(id_localidad=localidad)
            cliente = Cliente(
                nombre=nombre,
                apellido=apellido,
                username=username,
                telefono=telefono,
                direccion=direccion,
                correo=correo,
                password=password,
                id_localidad=localidad_obj,
                tipo_cuenta=Cliente.CLIENTE,
            )
            cliente.save()

            # Login del usuario después de la creación
            login(request, user)

            return redirect('home')  # Redirige a la página de inicio o donde quieras

        except IntegrityError:
            return render(request, 'base/registro.html', {'error': "Hubo un error al guardar los datos. Intenta nuevamente.", 'localidades': Localidad.objects.all()})

    # Si es GET, muestra el formulario de registro
    localidades = Localidad.objects.all()
    return render(request, 'base/registro.html', {'localidades': localidades})