from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views
from . import register_views

app_name = 'loyverse_integration'

# Configuración del router para la API REST
router = DefaultRouter()
router.register(r'connections', api_views.LoyverseConnectionViewSet, basename='loyverse-connection')

urlpatterns = [
    # URLs para vistas del backend
    path('connect/', views.connect_loyverse_view, name='connect_loyverse'),
    path('callback/', views.loyverse_callback_view, name='loyverse_callback'),
    path('dashboard/', views.sync_dashboard, name='sync_dashboard'),
    path('start-sync/', views.start_price_sync, name='start_price_sync'),
    
    # URLs para el flujo de registro con Loyverse
    path('register/', register_views.register_with_loyverse, name='register_with_loyverse'),
    path('register-callback/', register_views.loyverse_register_callback, name='loyverse_register_callback'),
    path('complete-registration/', register_views.complete_registration, name='complete_registration'),
    
    # API REST para frontend
    path('api/', include(router.urls)),
]
