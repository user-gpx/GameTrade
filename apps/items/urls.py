from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    path('', views.item_list, name='list'),
    path('sell/', views.item_create, name='create'),
    path('my/', views.my_items, name='my_items'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('<int:pk>/', views.item_detail, name='detail'),
    path('<int:pk>/edit/', views.item_edit, name='edit'),
    path('<int:pk>/delete/', views.item_delete, name='delete'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]
