from django.contrib import admin

from .models import TransactionLog


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'type', 'balance_after', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
