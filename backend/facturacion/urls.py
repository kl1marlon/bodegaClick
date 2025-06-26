from django.urls import path
from . import views
from . import views_tasks
from .views_info import DatabaseInfoView
from .views_actualizar_precios import ActualizarPreciosBaseAPIView
from .views_pdf import FacturaReportePDFView

urlpatterns = [
    # ... rutas existentes ...
    
    # Rutas para tareas asíncronas
    path('tareas/iniciar/', views_tasks.iniciar_tarea, name='iniciar_tarea'),
    path('tareas/estado/<str:task_id>/', views_tasks.estado_tarea, name='estado_tarea'),
    path('tareas/control/<str:task_id>/', views_tasks.control_tarea, name='control_tarea'),
    path('tareas/listado/', views_tasks.listar_tareas, name='listar_tareas'),
    
    # Ruta de prueba CORS
    path('test-cors/', views_tasks.test_cors, name='test_cors'),

    # Endpoint personalizado para actualizar precios base fuera del router
    path('api/actualizar-precios-base/', ActualizarPreciosBaseAPIView.as_view(), name='actualizar-precios-base'),

    # Endpoints de información y diagnóstico
    path('info/database/', DatabaseInfoView.as_view(), name='database-info'),
    
    # Endpoint para descargar reportes PDF de facturas
    path('facturas/descargar_reporte_pdf/', FacturaReportePDFView.as_view(), name='facturas-reporte-pdf'),
]