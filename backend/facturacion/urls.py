from django.urls import path
from . import views

urlpatterns = [
    # ... (otras urls de la app)
    path('tasas-actuales/', views.get_tasas_actuales, name='get_tasas_actuales'),
    path('recalcular-precios-base/', views.iniciar_recalculo_precios_base, name='iniciar_recalculo_precios_base'),
    path('loyverse/iniciar-sincronizacion/', views.iniciar_sincronizacion_loyverse, name='iniciar_sincronizacion_loyverse'),
    path('tasks/status/<str:task_id>/', views.get_task_status, name='get_task_status'),
]
