from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'buyer', 'seller', 'price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['item__name', 'buyer__username', 'seller__username']
