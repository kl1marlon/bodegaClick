from django.urls import path
from . import views
from . import views_tasks

urlpatterns = [
    # Rutas para facturas
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('facturas/<int:factura_id>/', views.detalle_factura, name='detalle_factura'),
    path('facturas/<int:factura_id>/sincronizar/', views.sincronizar_factura, name='sincronizar_factura'),
    path('facturas/<int:factura_id>/productos/<int:detalle_id>/', views.actualizar_producto_factura, name='actualizar_producto_factura'),
    path('facturas/<int:factura_id>/exportar/', views.exportar_factura, name='exportar_factura'),
    
    # Rutas para tareas asíncronas
    path('tareas/iniciar/', views_tasks.iniciar_tarea, name='iniciar_tarea'),
    path('tareas/estado/<str:task_id>/', views_tasks.estado_tarea, name='estado_tarea'),
    path('tareas/control/<str:task_id>/', views_tasks.control_tarea, name='control_tarea'),
    path('tareas/listado/', views_tasks.listar_tareas, name='listar_tareas'),
    
    # Ruta de prueba CORS
    path('test-cors/', views_tasks.test_cors, name='test_cors'),
] 