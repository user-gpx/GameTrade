from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'balance', 'created_at']
    search_fields = ['user__username', 'phone']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
