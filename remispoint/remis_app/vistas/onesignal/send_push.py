import requests

url = "https://api.onesignal.com/notifications?c=push"

mensaje = "Texto"
player_id = "2f64fbd7-836d-468f-985d-6c952b8669dd"

payload = {
    "app_id": "0406f65d-0560-4e90-94f4-f2c3a52f61f4",
    "contents": { "en": f'{mensaje}'},
    "include_player_ids": [player_id],
    
}
headers = {
    "accept": "application/json",
    "Authorization": "Key os_v2_app_aqdpmxifmbhjbfhu6lb2kl3b6r3c6ek5xhqezpfknrevwobojg4mnvxnjkexfpodgle2qbsjcthqhblwyxtkciic7yo3xsktqwrfxfi",
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)