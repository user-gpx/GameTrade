from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """道具分类"""
    name = models.CharField(max_length=50, unique=True, verbose_name='分类名称')
    description = models.TextField(blank=True, default='', verbose_name='分类描述')
    icon = models.CharField(max_length=50, blank=True, default='fas fa-tag', verbose_name='图标CSS类')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '道具分类'
        verbose_name_plural = '道具分类'
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """游戏道具"""

    class Status(models.TextChoices):
        ON_SALE = 'available', '在售'
        LOCKED = 'locked', '已锁定'
        SOLD = 'sold', '已售出'
        OFF_SHELF = 'off_shelf', '已下架'

    GAME_CHOICES = [
        ('lol', '英雄联盟'),
        ('csgo', 'CS:GO'),
        ('dota2', 'Dota 2'),
        ('genshin', '原神'),
        ('pubg', 'PUBG'),
        ('valorant', 'Valorant'),
        ('wow', '魔兽世界'),
        ('other', '其他'),
    ]

    name = models.CharField(max_length=200, verbose_name='道具名称')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='items', verbose_name='分类')
    game = models.CharField(max_length=20, choices=GAME_CHOICES, default='other', verbose_name='所属游戏')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    stock = models.PositiveIntegerField(default=1, verbose_name='库存')
    description = models.TextField(verbose_name='描述')
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name='道具图片')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items', verbose_name='卖家')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ON_SALE, verbose_name='状态')
    views_count = models.PositiveIntegerField(default=0, verbose_name='浏览次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '游戏道具'
        verbose_name_plural = '游戏道具'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_status_display_class(self):
        """返回状态对应的CSS类"""
        status_map = {
            self.Status.ON_SALE: 'bg-success',
            self.Status.SOLD: 'bg-secondary',
            self.Status.OFF_SHELF: 'bg-warning',
            self.Status.LOCKED: 'bg-warning',
        }
        return status_map.get(self.status, 'bg-secondary')


class Favorite(models.Model):
    """用户收藏"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='用户')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='道具')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')

    class Meta:
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
        unique_together = ['user', 'item']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 收藏了 {self.item.name}'
