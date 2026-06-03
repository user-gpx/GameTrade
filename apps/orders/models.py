import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from items.models import Item


class Order(models.Model):
    """平台统一订单模型，供交易、支付、订单管理和统计模块共同使用。"""

    STATUS_PENDING_PAYMENT = 'pending_payment'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, '待支付'),
        (STATUS_PAID, '待发货'),
        (STATUS_SHIPPED, '待收货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
    ]

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='orders', verbose_name='道具')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buy_orders', verbose_name='买家')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sell_orders', verbose_name='卖家')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='成交价')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT, verbose_name='订单状态')
    shipping_info = models.TextField(blank=True, default='', verbose_name='发货信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']

    def __str__(self):
        return f'订单#{self.pk} - {self.item.name}'

    def mark_paid(self):
        self.status = self.STATUS_PAID
        self.paid_at = timezone.now()
        self.item.status = 'sold'
        self.item.save(update_fields=['status'])
        self.save(update_fields=['status', 'paid_at', 'updated_at'])

    def mark_shipped(self, shipping_info):
        self.status = self.STATUS_SHIPPED
        self.shipping_info = shipping_info
        self.shipped_at = timezone.now()
        self.save(update_fields=['status', 'shipping_info', 'shipped_at', 'updated_at'])

    def mark_completed(self):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
