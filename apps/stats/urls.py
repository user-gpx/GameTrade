from django.urls import path
from . import views

app_name = 'stats'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/monthly/<int:pk>/', views.monthly_report_detail, name='monthly_report_detail'),
    path('reports/monthly/<int:pk>/send/', views.send_report_email, name='send_report_email'),
]
