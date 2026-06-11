import uuid

from django.db import migrations, models


def set_order_no(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.all():
        order.order_no = uuid.uuid4().hex[:16]
        order.save(update_fields=['order_no'])


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="order_no",
            field=models.CharField(
                blank=True, max_length=32, null=True, verbose_name="订单编号"
            ),
        ),
        migrations.RunPython(set_order_no, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="order_no",
            field=models.CharField(
                blank=True, max_length=32, unique=True, verbose_name="订单编号"
            ),
        ),
    ]
