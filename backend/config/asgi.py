import os
from django.core.asgi import get_asgi_application
from django.http import HttpResponse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Aplicación ASGI principal de Django
django_asgi_app = get_asgi_application()

# Middleware para manejar las solicitudes a /ws/notificaciones/
async def websocket_middleware(scope, receive, send):
    # Si es una solicitud a /ws/notificaciones/, devolver una respuesta vacía
    if scope['type'] == 'http' and scope['path'] == '/ws/notificaciones/':
        response = HttpResponse(status=200)
        await response(scope, receive, send)
        return
    
    # De lo contrario, pasar a la aplicación Django
    await django_asgi_app(scope, receive, send)

# Asignar el middleware como la aplicación ASGI
application = websocket_middleware 