from django.urls import path
from . import views
from . import views_tasks
from .views_info import DatabaseInfoView

urlpatterns = [
    # ... rutas existentes ...
    
    # Rutas para tareas asíncronas
    path('tareas/iniciar/', views_tasks.iniciar_tarea, name='iniciar_tarea'),
    path('tareas/estado/<str:task_id>/', views_tasks.estado_tarea, name='estado_tarea'),
    path('tareas/control/<str:task_id>/', views_tasks.control_tarea, name='control_tarea'),
    path('tareas/listado/', views_tasks.listar_tareas, name='listar_tareas'),
    
    # Ruta de prueba CORS
    path('test-cors/', views_tasks.test_cors, name='test_cors'),

    # Endpoints de información y diagnóstico
    path('info/database/', DatabaseInfoView.as_view(), name='database-info'),
] 