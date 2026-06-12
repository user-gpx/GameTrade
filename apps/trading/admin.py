from decimal import Decimal

from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from users.models import UserProfile

from .models import RechargeRequest, TransactionLog


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'type', 'balance_after', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)


@admin.register(RechargeRequest)
class RechargeRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_recharges', 'reject_recharges']
    list_editable = ()

    @transaction.atomic
    def approve_recharges(self, request, queryset):
        approved_count = 0
        for req in queryset.select_for_update().filter(status=RechargeRequest.Status.PENDING):
            profile, _ = UserProfile.objects.select_for_update().get_or_create(user=req.user)
            profile.balance = Decimal(profile.balance) + Decimal(req.amount)
            profile.save(update_fields=['balance'])

            TransactionLog.objects.create(
                user=req.user,
                amount=req.amount,
                type=TransactionLog.Type.CREDIT,
                balance_after=profile.balance,
            )

            req.status = RechargeRequest.Status.APPROVED
            req.reviewed_at = timezone.now()
            req.reviewed_by = request.user
            req.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
            approved_count += 1

        self.message_user(request, f'已通过 {approved_count} 条充值申请，余额已到账。', messages.SUCCESS)

    approve_recharges.short_description = '通过选中的充值申请（到账）'

    @transaction.atomic
    def reject_recharges(self, request, queryset):
        rejected_count = 0
        for req in queryset.select_for_update().filter(status=RechargeRequest.Status.PENDING):
            req.status = RechargeRequest.Status.REJECTED
            req.reviewed_at = timezone.now()
            req.reviewed_by = request.user
            req.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
            rejected_count += 1

        self.message_user(request, f'已拒绝 {rejected_count} 条充值申请。', messages.WARNING)

    reject_recharges.short_description = '拒绝选中的充值申请'
