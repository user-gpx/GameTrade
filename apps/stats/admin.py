from django.contrib import admin
from .models import MonthlyReport


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'created_at', 'emailed_at']
    list_filter = ['year', 'month', 'created_at']
    search_fields = ['user__username', 'content']
