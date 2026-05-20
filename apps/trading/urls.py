from django.urls import path

from . import views

urlpatterns = [
    path('order/create', views.create_order),
    path('order/cancel', views.cancel_order),
    path('order/ship', views.ship_order),
    path('order/confirm', views.confirm_receipt),
    path('seller/orders', views.seller_orders),
    path('payment/initiate', views.initiate_payment),
    path('payment/callback', views.payment_callback),
]
