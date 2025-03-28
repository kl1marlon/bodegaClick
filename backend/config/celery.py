import os
from celery import Celery

# Establecer la variable de entorno por defecto del settings module para el programa 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('bodegaClick')

# Usar settings del proyecto Django.
# La cadena 'config' es el nombre del paquete de la configuración del proyecto Django.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de módulos @shared_task
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 