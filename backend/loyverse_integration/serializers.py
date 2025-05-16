from rest_framework import serializers
from .models import LoyverseUserConnection

class LoyverseConnectionSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar el estado de la conexión con Loyverse.
    No expone tokens sensibles, solo información necesaria para el frontend.
    """
    account_name = serializers.CharField(source='loyverse_account_name', read_only=True)
    email = serializers.CharField(source='loyverse_email', read_only=True)
    token_status = serializers.SerializerMethodField()
    last_sync_time = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyverseUserConnection
        fields = [
            'id', 'account_name', 'email', 'is_active', 'token_status',
            'price_sync_status', 'last_sync_time', 'last_price_sync_details'
        ]
    
    def get_token_status(self, obj):
        """Determina si el token está válido, expirado o es inválido."""
        if not obj.is_active:
            return 'inactive'
        if obj.is_access_token_expired():
            return 'expired'
        return 'valid'
    
    def get_last_sync_time(self, obj):
        """Devuelve la fecha de la última sincronización."""
        return obj.last_price_sync_end_time

class SyncOptionsSerializer(serializers.Serializer):
    """
    Serializer para las opciones de sincronización de precios.
    """
    check_only = serializers.BooleanField(default=False, help_text="Si es true, solo verifica diferencias sin realizar cambios")
    force_lower_price = serializers.BooleanField(default=False, help_text="Si es true, actualiza incluso si el precio local es menor que el de Loyverse")
    recalculate_first = serializers.BooleanField(default=False, help_text="Si es true, recalcula precios base primero usando tasa de cambio actual")
