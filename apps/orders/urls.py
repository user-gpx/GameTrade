from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('items/<int:item_id>/buy/', views.create_order, name='create_order'),
    path('buyer/', views.buyer_orders, name='buyer_orders'),
    path('seller/', views.seller_orders, name='seller_orders'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/pay/', views.pay_order, name='pay_order'),
    path('<int:pk>/ship/', views.ship_order, name='ship_order'),
    path('<int:pk>/confirm/', views.confirm_receive, name='confirm_receive'),
]
