from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TransactionLog(models.Model):
    class Type(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_logs')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=Type.choices)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.user_id}:{self.type}:{self.amount}"


class RechargeRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待审核'
        APPROVED = 'approved', '已通过'
        REJECTED = 'rejected', '已拒绝'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recharge_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='充值金额')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name='状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='申请时间')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_recharges', verbose_name='审核人')
    out_trade_no = models.CharField(max_length=64, unique=True, null=True, blank=True, verbose_name='商户订单号')
    trade_no = models.CharField(max_length=64, null=True, blank=True, verbose_name='支付宝交易号')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '充值申请'
        verbose_name_plural = '充值申请'

    def __str__(self) -> str:
        return f"{self.user.username} - ¥{self.amount} - {self.get_status_display()}"
