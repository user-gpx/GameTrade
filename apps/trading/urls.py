from django.urls import path

from . import views

urlpatterns = [
    path('buy_now', views.buy_now),
    path('order/create', views.create_order),
    path('order/cancel', views.cancel_order),
    path('order/ship', views.ship_order),
    path('order/confirm', views.confirm_receipt),
    path('orders/buyer', views.buyer_order_page, name='buyer_orders'),
    path('orders/seller', views.seller_order_page, name='seller_orders'),
    path('buyer/orders', views.buyer_orders),
    path('seller/orders', views.seller_orders),
    path('recharge', views.recharge, name='recharge'),
    path('payment/initiate', views.initiate_payment),
    path('payment/callback', views.payment_callback),
]
