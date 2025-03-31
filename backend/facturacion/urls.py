from django.urls import path
from . import views
from . import views_tasks

urlpatterns = [
    # ... rutas existentes ...
    
    # Rutas para tareas asíncronas
    path('api/tareas/iniciar/', views_tasks.iniciar_tarea, name='iniciar_tarea'),
    path('api/tareas/estado/<str:task_id>/', views_tasks.estado_tarea, name='estado_tarea'),
    path('api/tareas/control/<str:task_id>/', views_tasks.control_tarea, name='control_tarea'),
    path('api/tareas/listado/', views_tasks.listar_tareas, name='listar_tareas'),
    
    # Ruta de prueba CORS
    path('api/test-cors/', views_tasks.test_cors, name='test_cors'),
] 