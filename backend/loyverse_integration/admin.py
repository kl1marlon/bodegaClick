from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import LoyverseUserConnection


@admin.register(LoyverseUserConnection)
class LoyverseUserConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'loyverse_account_name', 'loyverse_email', 'is_active', 'token_status', 
                   'price_sync_status', 'last_sync_time', 'updated_at')
    list_display_links = ('user', 'loyverse_account_name')
    readonly_fields = ('access_token', 'refresh_token', 'created_at', 'updated_at', 'token_status')
    list_filter = ('is_active', 'price_sync_status')
    search_fields = ('user__username', 'user__email', 'loyverse_account_name', 'loyverse_email', 'loyverse_user_subject')
    date_hierarchy = 'created_at'
    actions = ['mark_as_active', 'mark_as_inactive']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'is_active')
        }),
        ('Información de Loyverse', {
            'fields': ('loyverse_user_subject', 'loyverse_account_name', 'loyverse_email')
        }),
        ('Tokens y Autenticación', {
            'fields': ('access_token', 'refresh_token', 'token_type', 'expires_at', 'token_status', 'scope', 'last_token_refresh_time')
        }),
        ('Estado de Sincronización', {
            'fields': ('price_sync_status', 'last_price_sync_start_time', 'last_price_sync_end_time', 'last_price_sync_details')
        }),
        ('Errores', {
            'fields': ('last_error_message',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def token_status(self, obj):
        """Muestra el estado del token con formato de color."""
        if not obj.is_active:
            return format_html('<span style="color: red;">Inactivo</span>')
        
        if obj.is_access_token_expired():
            return format_html('<span style="color: orange;">Expirado</span>')
        
        # Calcular tiempo restante
        if obj.expires_at:
            time_left = obj.expires_at - timezone.now()
            hours_left = time_left.total_seconds() / 3600
            
            if hours_left < 1:
                return format_html('<span style="color: orange;">Expira pronto</span>')
            else:
                return format_html('<span style="color: green;">Válido</span>')
        
        return format_html('<span style="color: gray;">Desconocido</span>')
    
    token_status.short_description = 'Estado del Token'
    
    def last_sync_time(self, obj):
        """Muestra la última vez que se sincronizó."""
        if obj.last_price_sync_end_time:
            return obj.last_price_sync_end_time
        return '-'
    
    last_sync_time.short_description = 'Última Sincronización'
    
    def mark_as_active(self, request, queryset):
        """Marca las conexiones seleccionadas como activas."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} conexiones marcadas como activas.')
    
    mark_as_active.short_description = "Marcar conexiones seleccionadas como activas"
    
    def mark_as_inactive(self, request, queryset):
        """Marca las conexiones seleccionadas como inactivas."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} conexiones marcadas como inactivas.')
    
    mark_as_inactive.short_description = "Marcar conexiones seleccionadas como inactivas"
