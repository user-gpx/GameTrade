from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from items.models import Category, Favorite, Item
from orders.models import Order
from .models import MonthlyReport


class MonthlyReportTestCase(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', password='TestPass123!')
        self.buyer = User.objects.create_user(username='buyer', password='TestPass123!', email='buyer@example.com')
        self.category = Category.objects.create(name='武器')
        self.item = Item.objects.create(
            name='传说之剑',
            category=self.category,
            game='other',
            price=188.00,
            description='测试道具',
            seller=self.seller,
        )

    def test_monthly_report_generation(self):
        Favorite.objects.create(user=self.buyer, item=self.item)
        order = Order.objects.create(
            item=self.item,
            buyer=self.buyer,
            seller=self.seller,
            price=self.item.price,
            status=Order.STATUS_COMPLETED,
            completed_at=timezone.now(),
        )
        self.assertEqual(order.status, Order.STATUS_COMPLETED)

        self.client.login(username='buyer', password='TestPass123!')
        now = timezone.localtime()
        response = self.client.post(reverse('stats:monthly_report'), {
            'year': now.year,
            'month': now.month,
        })
        report = MonthlyReport.objects.get(user=self.buyer, year=now.year, month=now.month)
        self.assertRedirects(response, reverse('stats:monthly_report_detail', args=[report.id]))
        self.assertIn('交易月报', report.content)
        self.assertIn('传说之剑', report.content)
