import requests

def enviar_notificacion(mensaje, player_id):
    url = "https://api.onesignal.com/notifications?c=push"
    
    payload = {
        "app_id": "0406f65d-0560-4e90-94f4-f2c3a52f61f4",
        "contents": {"en": mensaje},
        "include_player_ids": [player_id],
    }
    
    headers = {
        "accept": "application/json",
        "Authorization": "Key os_v2_app_aqdpmxifmbhjbfhu6lb2kl3b6r3c6ek5xhqezpfknrevwobojg4mnvxnjkexfpodgle2qbsjcthqhblwyxtkciic7yo3xsktqwrfxfi",
        "content-type": "application/json",
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    return response.json()  # Retorna la respuesta en formato JSON
