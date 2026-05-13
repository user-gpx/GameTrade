from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """用户资料扩展模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机号')
    bio = models.TextField(max_length=500, blank=True, default='', verbose_name='个人简介')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='账户余额')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f'{self.user.username} 的资料'

    def get_avatar_url(self):
        """获取头像URL，无头像时返回默认头像"""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default_avatar.png'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """创建用户时自动创建对应的资料"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用户时自动保存资料"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
