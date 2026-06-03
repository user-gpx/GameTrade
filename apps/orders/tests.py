from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from items.models import Category, Item
from .models import Order


class OrderFlowTestCase(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', password='TestPass123!')
        self.buyer = User.objects.create_user(username='buyer', password='TestPass123!')
        self.category = Category.objects.create(name='武器')
        self.item = Item.objects.create(
            name='传说之剑',
            category=self.category,
            game='other',
            price=188.00,
            description='测试道具',
            seller=self.seller,
        )

    def test_order_status_flow(self):
        self.client.login(username='buyer', password='TestPass123!')
        response = self.client.get(reverse('orders:create_order', args=[self.item.id]))
        order = Order.objects.get(item=self.item, buyer=self.buyer)
        self.assertRedirects(response, reverse('orders:detail', args=[order.id]))
        self.assertEqual(order.status, Order.STATUS_PENDING_PAYMENT)

        self.client.post(reverse('orders:pay_order', args=[order.id]))
        order.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertEqual(self.item.status, 'sold')

        self.client.logout()
        self.client.login(username='seller', password='TestPass123!')
        self.client.post(reverse('orders:ship_order', args=[order.id]), {'shipping_info': '顺丰 SF123456'})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_SHIPPED)

        self.client.logout()
        self.client.login(username='buyer', password='TestPass123!')
        self.client.post(reverse('orders:confirm_receive', args=[order.id]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)
