from django.db import models
from django.contrib.auth.models import User


class MonthlyReport(models.Model):
    """保存手动生成的月度统计快照，方便演示和邮件发送。"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports', verbose_name='用户')
    year = models.PositiveIntegerField(verbose_name='年份')
    month = models.PositiveIntegerField(verbose_name='月份')
    content = models.TextField(verbose_name='报告内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    emailed_at = models.DateTimeField(null=True, blank=True, verbose_name='发送时间')

    class Meta:
        verbose_name = '月报'
        verbose_name_plural = '月报'
        ordering = ['-created_at']
        unique_together = ['user', 'year', 'month']

    def __str__(self):
        return f'{self.user.username} {self.year}-{self.month:02d} 月报'
