import urllib.parse
from django.shortcuts import redirect
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from remis_app.models import *
import requests
import json
from django.views.decorators.csrf import csrf_exempt

def conectar_mercadopago(request):
    """Redirige al usuario a la autorización de Mercado Pago SIN PKCE"""
    user = request.user
    if not user.is_authenticated:
        return redirect('login')

    auth_url = (
        f"https://auth.mercadopago.com/authorization"
        f"?response_type=code"
        f"&client_id={settings.MP_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(settings.MP_REDIRECT_URI)}"
        f"&scope=offline_access%20read"
    )

    return redirect(auth_url)



@login_required
def mercadopago_callback(request):
    """Captura el código de autorización, obtiene el user_id del chofer y lo guarda"""
    if 'code' not in request.GET:
        return JsonResponse({'error': 'No authorization code provided'}, status=400)

    auth_code = request.GET['code']

    # URL de Mercado Pago para obtener el mp_user_id
    token_url = "https://api.mercadopago.com/oauth/token"

    data = {
        'client_id': settings.MP_CLIENT_ID,
        'client_secret': settings.MP_CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.MP_REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code != 200:
        print("ERROR Mercado Pago:", response.json())  # ✅ Ver qué está fallando exactamente
        return JsonResponse({
            'error': 'Failed to obtain access token',
            'status_code': response.status_code,
            'response': response.json()
        }, status=400)

    token_data = response.json()
    mp_user_id = token_data.get('user_id')  # ✅ Obtenemos el mp_user_id del chofer

    # 📌 PASO 1: Buscar el cliente usando el email del usuario autenticado
    try:
        cliente = Cliente.objects.get(correo=request.user.email)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=400)

    # 📌 PASO 2: Buscar el chofer asociado al cliente
    try:
        chofer = Chofer.objects.get(id_cliente=cliente.id_cliente)
    except Chofer.DoesNotExist:
        return JsonResponse({'error': 'Chofer no encontrado'}, status=400)

    # 📌 PASO 3: Asignar el nuevo mp_user_id y guardar
    chofer.mp_user_id = mp_user_id
    chofer.save()

    return redirect('chofer')  # Redirigir al panel del chofer


@csrf_exempt
def mp_webhook(request):
    """Procesa las notificaciones de pago de MercadoPago."""
    try:
        data = json.loads(request.body)
        external_reference = data.get("external_reference")
        payment_status = data.get("status")

        if external_reference and payment_status:
            viaje = Viaje.objects.get(id_viaje=external_reference)
            if payment_status == "approved":
                viaje.estado = "Pago Confirmado"
                viaje.save(update_fields=["estado"])

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def pagos_exitoso(request, id_viaje):
    """Vista cuando el pago se completa con éxito."""
    return render(request, "clientes/pagos_exitoso.html", {"id_viaje": id_viaje})

@login_required
def pagos_fallido(request, id_viaje):
    """Vista cuando el pago falla."""
    return render(request, "clientes/pagos_fallido.html", {"id_viaje": id_viaje})

@login_required
def pagos_pendiente(request, id_viaje):
    """Vista cuando el pago queda pendiente."""
    return render(request, "clientes/pagos_pendiente.html", {"id_viaje": id_viaje})