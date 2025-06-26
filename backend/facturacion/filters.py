import django_filters
from .models import Factura

class FacturaDateFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name='fecha', lookup_expr='date__gte')
    fecha_hasta = django_filters.DateFilter(field_name='fecha', lookup_expr='date__lte')

    class Meta:
        model = Factura
        fields = ['fecha_desde', 'fecha_hasta']
