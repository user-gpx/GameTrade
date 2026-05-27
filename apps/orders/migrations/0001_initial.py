# Generated manually for orders app.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='成交价')),
                ('status', models.CharField(choices=[('pending_payment', '待支付'), ('paid', '待发货'), ('shipped', '待收货'), ('completed', '已完成'), ('cancelled', '已取消')], default='pending_payment', max_length=30, verbose_name='订单状态')),
                ('shipping_info', models.TextField(blank=True, default='', verbose_name='发货信息')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='支付时间')),
                ('shipped_at', models.DateTimeField(blank=True, null=True, verbose_name='发货时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buy_orders', to=settings.AUTH_USER_MODEL, verbose_name='买家')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='items.item', verbose_name='道具')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sell_orders', to=settings.AUTH_USER_MODEL, verbose_name='卖家')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'ordering': ['-created_at'],
            },
        ),
    ]
