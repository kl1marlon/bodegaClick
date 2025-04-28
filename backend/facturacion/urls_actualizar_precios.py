from django.urls import path
from .views_actualizar_precios import ActualizarPreciosBaseAPIView

urlpatterns = [
    path('productos/actualizar-precios-base/', ActualizarPreciosBaseAPIView.as_view(), name='actualizar-precios-base'),
]
