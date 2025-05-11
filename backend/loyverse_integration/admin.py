from django.contrib import admin
from .models import LoyverseUserConnection


@admin.register(LoyverseUserConnection)
class LoyverseUserConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'loyverse_account_name', 'is_active', 'price_sync_status', 'updated_at')
    readonly_fields = ('access_token', 'refresh_token', 'created_at', 'updated_at') # Consider making tokens readonly
    list_filter = ('is_active', 'price_sync_status')
    search_fields = ('user__username', 'loyverse_account_name', 'loyverse_email')

# Register your models here.
