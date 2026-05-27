import uuid

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', '待支付'
        PAID = 'paid', '已支付'
        SHIPPED = 'shipped', '已发货'
        COMPLETED = 'completed', '已完成'
        CANCELED = 'canceled', '已取消'

    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单号')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buy_orders', verbose_name='买家')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sell_orders', verbose_name='卖家')
    item = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='orders', verbose_name='道具')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='成交价')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        ordering = ['-created_at']

    def __str__(self):
        return f'订单 {self.order_no}'

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = uuid.uuid4().hex[:16]
        super().save(*args, **kwargs)
