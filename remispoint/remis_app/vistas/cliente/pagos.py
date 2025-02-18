import json
import mercadopago
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from remis_app.models import Viaje, Chofer

@login_required
def pagos(request, id_viaje):
    """Vista para mostrar el resumen del viaje y generar el pago si es con MercadoPago."""
    print(f"🔎 Buscando viaje con ID: {id_viaje}")
    viaje = get_object_or_404(Viaje, id_viaje=id_viaje)
    print(f"✅ Viaje encontrado: {viaje}")

    preference_id = None
    if viaje.cod_tipo_pago.cod_tipo_pago == 3:
        print("✅ El método de pago es MercadoPago.")
        chofer = get_object_or_404(Chofer, id_chofer=viaje.id_chofer.id_chofer)
        print(f"🔎 Buscando chofer con ID: {viaje.id_chofer.id_chofer}")

        if chofer.mp_user_id:
            print(f"✅ Chofer encontrado con MP_USER_ID: {chofer.mp_user_id}")

            try:
                sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
                print(f"🔎 Usando ACCESS_TOKEN: {settings.MP_ACCESS_TOKEN}")

                preference_data = {
                    "items": [
                        {
                            "title": "Pago del viaje",
                            "quantity": 1,
                            "currency_id": "ARS",
                            "unit_price": float(viaje.id_precio.precio)
                        }
                    ],
                    "payer": {
                        "email": request.user.email
                    },
                    "collector_id": int(chofer.mp_user_id) if chofer.mp_user_id else None,
                    "external_reference": str(viaje.id_viaje),
                    "notification_url": f"{settings.SITE_URL}/mp_webhook/",
                    "auto_return": "approved",
                    "back_urls": {
                        "success": f"{settings.SITE_URL}/pagos_exitoso/{viaje.id_viaje}/",
                        "failure": f"{settings.SITE_URL}/pagos_fallido/{viaje.id_viaje}/",
                        "pending": f"{settings.SITE_URL}/pagos_pendiente/{viaje.id_viaje}/"
                    }
                }

                print("🔎 Datos enviados a MercadoPago:", json.dumps(preference_data, indent=4))

                preference_response = sdk.preference().create(preference_data)
                print("🔎 Respuesta completa de MercadoPago:", preference_response)

                if "response" in preference_response and "id" in preference_response["response"]:
                    preference_id = preference_response["response"]["id"]
                    print(f"✅ Preference ID generado correctamente: {preference_id}")
                else:
                    print("🚨 Error: No se pudo obtener preference_id de MercadoPago.")
                    print(f"❌ Respuesta de MercadoPago: {preference_response}")

            except Exception as e:
                print(f"🚨 Error al generar la preferencia de pago: {str(e)}")

    return render(request, "clientes/pagos.html", {"viaje": viaje, "preference_id": preference_id})