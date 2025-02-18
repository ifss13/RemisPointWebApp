from django.urls import path
from . import *

urlpatterns = [
    path('mercadopago/conectar/', conectar_mercadopago, name='conectar_mercadopago'),  # MercadoPago Chofer
    path('mercadopago/callback/', mercadopago_callback, name='mercadopago_callback'),  # MercadoPago
    path('mp_webhook/', mp_webhook, name='mp_webhook'),  # MercadoPago
    path('pagos_exitoso/<int:id_viaje>/', pagos_exitoso, name='pagos_exitoso'),  # Cliente
    path('pagos_fallido/<int:id_viaje>/', pagos_fallido, name='pagos_fallido'),  # Cliente
    path('pagos_pendiente/<int:id_viaje>/', pagos_pendiente, name='pagos_pendiente'),  # Cliente
]