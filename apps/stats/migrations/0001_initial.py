# Generated manually for stats app.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(verbose_name='年份')),
                ('month', models.PositiveIntegerField(verbose_name='月份')),
                ('content', models.TextField(verbose_name='报告内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='生成时间')),
                ('emailed_at', models.DateTimeField(blank=True, null=True, verbose_name='发送时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_reports', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '月报',
                'verbose_name_plural': '月报',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'year', 'month')},
            },
        ),
    ]
