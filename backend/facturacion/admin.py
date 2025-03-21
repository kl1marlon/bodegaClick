from django.contrib import admin
from .models import Producto, TasaCambio, Factura, DetalleFactura, Webhook

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'precio_compra_usd', 'unidades_paquete', 'fuente_actualizacion', 'ultima_actualizacion_precio')
    list_filter = ('categoria', 'fuente_actualizacion')
    search_fields = ('nombre', 'loyverse_id')
    readonly_fields = ('loyverse_id', 'ultima_actualizacion_precio', 'updated_at', 'created_at')

@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'valor', 'fecha')
    list_filter = ('tipo',)

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'moneda', 'total_bs', 'total_usd', 'sincronizado_loyverse')
    list_filter = ('moneda', 'sincronizado_loyverse')
    search_fields = ('numero',)

@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'producto', 'cantidad', 'precio_unitario', 'total')
    list_filter = ('factura',)
    search_fields = ('producto__nombre',)

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'url', 'status', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('id', 'url') 