from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import Client

from items.models import Item
from orders.models import Order
from users.models import UserProfile

# Create your tests here.

User = get_user_model()


class TradingFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='x')
        self.buyer = User.objects.create_user(username='buyer', password='x')
        UserProfile.objects.get_or_create(user=self.seller)
        UserProfile.objects.get_or_create(user=self.buyer)

        self.item = Item.objects.create(
            name='item1',
            price='10.00',
            seller=self.seller,
            status=Item.Status.ON_SALE,
            stock=1,
        )

    def test_full_flow(self):
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        self.assertEqual(r.status_code, 200)
        order_id = r.json()['order_id']

        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id, 'pay_method': 'mock'})
        self.assertEqual(r.status_code, 200)
        payment_no = r.json()['payment_no']

        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        self.assertEqual(r.status_code, 200)

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.Status.PAID)

        r = self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)

        r = self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)

        seller_profile = UserProfile.objects.get(user=self.seller)
        self.assertEqual(str(seller_profile.balance), '10.00')

    def test_cancel_flow(self):
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/order/cancel', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertEqual(r.status_code, 200)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.Status.CANCELED)

        item = Item.objects.get(id=self.item.id)
        self.assertEqual(item.stock, 1)
        self.assertEqual(item.status, Item.Status.ON_SALE)
