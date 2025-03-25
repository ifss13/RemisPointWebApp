# remis_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()  # Acepta la conexión WebSocket
        await self.send(text_data=json.dumps({"message": "¡Conexión exitosa!"}))

    async def disconnect(self, close_code):
        print(f"Desconectado con código: {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")

        # Responder al cliente WebSocket
        await self.send(text_data=json.dumps({
            "response": f"Recibido: {message}"
        }))


from channels.generic.websocket import AsyncWebsocketConsumer
import json

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Se ejecuta cuando un chofer se conecta al WebSocket."""
        await self.accept()
        self.room_group_name = "ubicaciones"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def disconnect(self, close_code):
        """Se ejecuta cuando el chofer se desconecta."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Recibe datos de ubicación del chofer y los retransmite."""
        data = json.loads(text_data)
        chofer_id = data.get("chofer_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        viaje_id = data.get("viaje_id")
        print(data)
        
        # Retransmitir la ubicación a todos los clientes interesados
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_location",
                "chofer_id": chofer_id,
                "latitude": latitude,
                "longitude": longitude,
                "viaje_id": viaje_id
            }
        )

    async def send_location(self, event):
        """Envía la ubicación actualizada a los clientes."""
        await self.send(text_data=json.dumps({
            "chofer_id": event["chofer_id"],
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "viaje_id": event["viaje_id"]
        }))

class BaseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("base", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("base", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "ubicacion_chofer":
            await self.channel_layer.group_send(
                "base",
                {
                    "type": "send_location",
                    "chofer_id": data["chofer_id"],
                    "nombre": data["nombre"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"]
                }
            )


    async def send_location(self, event):
        await self.send(text_data=json.dumps(event))

