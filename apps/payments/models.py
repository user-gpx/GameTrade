import uuid

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待支付'
        SUCCESS = 'success', '支付成功'
        FAILED = 'failed', '支付失败'

    payment_no = models.CharField(max_length=32, unique=True, verbose_name='支付单号')
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment', verbose_name='订单')
    pay_method = models.CharField(max_length=20, default='mock', verbose_name='支付方式')
    pay_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='支付状态')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='支付金额')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '支付记录'
        verbose_name_plural = '支付记录'
        ordering = ['-created_at']

    def __str__(self):
        return f'支付 {self.payment_no}'

    def save(self, *args, **kwargs):
        if not self.payment_no:
            self.payment_no = uuid.uuid4().hex[:16]
        if self.amount == 0 and self.order_id:
            self.amount = self.order.price
        super().save(*args, **kwargs)

    def mark_success(self):
        self.pay_status = self.Status.SUCCESS
        self.save(update_fields=['pay_status'])

    def mark_failed(self):
        self.pay_status = self.Status.FAILED
        self.save(update_fields=['pay_status'])
