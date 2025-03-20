import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Producto

class NotificacionesConsumer(AsyncWebsocketConsumer):
    """
    Consumer para notificaciones en tiempo real
    """
    async def connect(self):
        """
        Cuando un cliente se conecta al WebSocket
        """
        # Unirse al grupo de notificaciones de inventario
        await self.channel_layer.group_add(
            "inventario_updates",
            self.channel_name
        )
        
        # Aceptar la conexión
        await self.accept()
        
        # Enviar mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al sistema de notificaciones'
        }))
    
    async def disconnect(self, close_code):
        """
        Cuando un cliente se desconecta del WebSocket
        """
        # Abandonar el grupo de notificaciones
        await self.channel_layer.group_discard(
            "inventario_updates",
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Recibir mensajes del WebSocket
        """
        # No esperamos recibir mensajes del cliente en este caso
        pass
    
    async def inventory_update(self, event):
        """
        Enviar notificación de actualización de inventario al WebSocket
        """
        # Enviar el mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'inventory_update',
            'producto': event['producto'],
            'stock_actual': event['stock_actual'],
            'message': event['message']
        })) 