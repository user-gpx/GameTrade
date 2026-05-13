from django.contrib import admin
from django.urls import path
from django.shortcuts import HttpResponse
from apps.stats import views as views  # ✅ 现在可以直接导入 stats
urlpatterns = [
    path('',views.dash),
]