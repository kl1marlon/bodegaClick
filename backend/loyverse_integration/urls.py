from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

app_name = 'loyverse_integration'

# Configuración del router para la API REST
router = DefaultRouter()
router.register(r'api/connections', api_views.LoyverseConnectionViewSet, basename='loyverse-connection')

urlpatterns = [
    # URLs para vistas del backend
    path('connect/', views.connect_loyverse_view, name='connect_loyverse'),
    path('callback/', views.loyverse_callback_view, name='loyverse_callback'),
    path('dashboard/', views.sync_dashboard, name='sync_dashboard'),
    path('start-sync/', views.start_price_sync, name='start_price_sync'),
    
    # API REST para frontend
    path('', include(router.urls)),
]
