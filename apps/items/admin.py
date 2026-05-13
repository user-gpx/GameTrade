from django.contrib import admin
from .models import Category, Item, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'price', 'seller', 'status', 'views_count', 'created_at']
    list_filter = ['status', 'game', 'category', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['status']
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'created_at']
    list_filter = ['created_at']
