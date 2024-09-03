from channels.generic.websocket import AsyncWebsocketConsumer
import json


class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "new_mail_goup",
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Подключение установлено!'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "new_mail_goup",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def send_email(self, event):
        email_data = event['email_data']
        await self.send(text_data=json.dumps({
            'type': 'email',
            'email_data': email_data
            }))

    async def upadate_progress(self, event):
        progress = event['progress']
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'progress': progress
        }))
