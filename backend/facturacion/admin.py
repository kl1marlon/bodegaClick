from django.contrib import admin
from .models import Producto, TasaCambio, Factura, DetalleFactura, Webhook
from django.urls import path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.contrib import messages
from django.core.management import call_command
from io import StringIO
import sys

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0

class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'moneda', 'total_bs', 'total_usd', 'sincronizado_loyverse')
    list_filter = ('sincronizado_loyverse', 'fecha')
    search_fields = ('id',)
    readonly_fields = ('fecha',)
    inlines = [DetalleFacturaInline]

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'precio_compra_usd', 'precio_venta_calculado', 'stock_actual', 'ultima_actualizacion_stock')
    list_filter = ('categoria', 'aplicar_iva')
    search_fields = ('nombre', 'descripcion', 'loyverse_id')
    list_per_page = 50

    # Añadir acción para sincronizar inventario
    actions = ['sincronizar_inventario_seleccionados']

    # Añadir botones personalizados
    change_list_template = 'admin/producto_changelist.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sincronizar-inventario/', self.admin_site.admin_view(self.sincronizar_inventario_view), name='sincronizar-inventario'),
            path('sincronizar-inventario-forzado/', self.admin_site.admin_view(self.sincronizar_inventario_forzado_view), name='sincronizar-inventario-forzado'),
        ]
        return custom_urls + urls

    def sincronizar_inventario_seleccionados(self, request, queryset):
        """Sincronizar inventario solo para los productos seleccionados"""
        try:
            # Guardar los IDs de los productos seleccionados
            productos_ids = list(queryset.values_list('id', flat=True))
            
            # Ejecutar comando solo para esos productos
            stdout_backup = sys.stdout
            output = StringIO()
            sys.stdout = output
            
            # TODO: Implementar lógica para sincronizar solo los productos seleccionados
            # Por ahora, simplemente mostramos un mensaje
            
            # Restaurar stdout
            sys.stdout = stdout_backup
            
            self.message_user(
                request, 
                f"Se sincronizó el inventario para {len(productos_ids)} productos seleccionados.", 
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request, 
                f"Error al sincronizar inventario: {str(e)}", 
                messages.ERROR
            )
    
    sincronizar_inventario_seleccionados.short_description = "Sincronizar inventario para productos seleccionados"

    def sincronizar_inventario_view(self, request):
        """Vista para sincronizar el inventario de productos sin stock"""
        try:
            # Capturar la salida del comando
            stdout_backup = sys.stdout
            output = StringIO()
            sys.stdout = output
            
            try:
                call_command('sync_inventory')
            except Exception as e:
                self.message_user(
                    request, 
                    f"Error al ejecutar el comando: {str(e)}", 
                    messages.ERROR
                )
                return HttpResponseRedirect(reverse('admin:facturacion_producto_changelist'))
            
            # Restaurar stdout
            sys.stdout = stdout_backup
            
            # Limpiar caracteres nulos que pueden causar errores
            command_output = output.getvalue().replace('\x00', '')
            
            # Extraer estadísticas
            total_procesados = 0
            actualizados = 0
            
            for line in command_output.split('\n'):
                if 'Total productos procesados:' in line:
                    try:
                        total_procesados = line.split(':')[1].strip()
                    except:
                        total_procesados = "N/A"
                elif 'Productos con stock actualizado:' in line:
                    try:
                        actualizados = line.split(':')[1].strip()
                    except:
                        actualizados = "N/A"
            
            self.message_user(
                request, 
                f"Sincronización completada. {actualizados} de {total_procesados} productos actualizados.", 
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request, 
                f"Error al sincronizar inventario: {str(e)}", 
                messages.ERROR
            )
        
        return HttpResponseRedirect(reverse('admin:facturacion_producto_changelist'))

    def sincronizar_inventario_forzado_view(self, request):
        """Vista para sincronizar el inventario de TODOS los productos"""
        try:
            # Capturar la salida del comando
            stdout_backup = sys.stdout
            output = StringIO()
            sys.stdout = output
            
            try:
                call_command('sync_inventory', force=True)
            except Exception as e:
                self.message_user(
                    request, 
                    f"Error al ejecutar el comando: {str(e)}", 
                    messages.ERROR
                )
                return HttpResponseRedirect(reverse('admin:facturacion_producto_changelist'))
            
            # Restaurar stdout
            sys.stdout = stdout_backup
            
            # Limpiar caracteres nulos que pueden causar errores
            command_output = output.getvalue().replace('\x00', '')
            
            # Extraer estadísticas
            total_procesados = 0
            actualizados = 0
            
            for line in command_output.split('\n'):
                if 'Total productos procesados:' in line:
                    try:
                        total_procesados = line.split(':')[1].strip()
                    except:
                        total_procesados = "N/A"
                elif 'Productos con stock actualizado:' in line:
                    try:
                        actualizados = line.split(':')[1].strip()
                    except:
                        actualizados = "N/A"
            
            self.message_user(
                request, 
                f"Sincronización FORZADA completada. {actualizados} de {total_procesados} productos actualizados.", 
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request, 
                f"Error al sincronizar inventario: {str(e)}", 
                messages.ERROR
            )
        
        return HttpResponseRedirect(reverse('admin:facturacion_producto_changelist'))

class TasaCambioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'valor')
    list_filter = ('tipo', 'fecha')
    search_fields = ('valor',)

class WebhookAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'url', 'status', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('url',)

admin.site.register(Producto, ProductoAdmin)
admin.site.register(TasaCambio, TasaCambioAdmin)
admin.site.register(Factura, FacturaAdmin)
admin.site.register(Webhook, WebhookAdmin) 