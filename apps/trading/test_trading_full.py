"""
Trading模块完整黑盒测试（Django TestCase）
覆盖：一步购买、创建订单、取消订单、支付管理、卖家发货、确认收货、账户充值
测试方法：等价类划分、边界值分析、判定表
"""
import threading
import time
from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.db import transaction

from items.models import Item
from orders.models import Order
from payments.models import Payment
from users.models import UserProfile
from trading.models import TransactionLog

User = get_user_model()


class BuyNowTests(TestCase):
    """F1: 一步购买 —— 等价类 + 边界值"""

    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller_f1', password='x')
        self.buyer = User.objects.create_user(username='buyer_f1', password='x')
        UserProfile.objects.get_or_create(user=self.seller)
        self.buyer_profile, _ = UserProfile.objects.get_or_create(user=self.buyer)

    def _create_item(self, **kwargs):
        defaults = {
            'name': 'test_item', 'price': '10.00', 'seller': self.seller,
            'status': Item.Status.ON_SALE, 'stock': 1,
        }
        defaults.update(kwargs)
        return Item.objects.create(**defaults)

    # ---- 等价类：正常流程 ----
    def test_F101_normal_buy_single_stock(self):
        """F1-01: 正常购买（stock=1），购买后item变SOLD"""
        item = self._create_item(stock=1, price='10.00')
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertTrue(data['ok'], msg=f"Expected ok=true, got: {data}")
        self.assertEqual(data['status'], 'paid')

        item.refresh_from_db()
        self.assertEqual(item.stock, 0)
        self.assertEqual(item.status, Item.Status.SOLD)

        self.buyer_profile.refresh_from_db()
        self.assertEqual(str(self.buyer_profile.balance), '90.00')

        log = TransactionLog.objects.filter(user=self.buyer).last()
        self.assertEqual(log.type, TransactionLog.Type.DEBIT)
        self.assertEqual(str(log.amount), '10.00')

    def test_F102_normal_buy_multi_stock(self):
        """F1-02: 正常购买（stock>1），item保持ON_SALE"""
        item = self._create_item(stock=3, price='10.00')
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertTrue(data['ok'])
        item.refresh_from_db()
        self.assertEqual(item.stock, 2)
        self.assertEqual(item.status, Item.Status.ON_SALE)

    # ---- 边界值：余额 ----
    def test_F103_balance_exact_equal(self):
        """F1-03: 余额刚好等于价格"""
        item = self._create_item(price='10.00')
        self.buyer_profile.balance = Decimal('10.00')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.buyer_profile.refresh_from_db()
        self.assertEqual(str(self.buyer_profile.balance), '0.00')

    def test_F104_balance_one_cent_above(self):
        """F1-04: 余额比价格多0.01"""
        item = self._create_item(price='10.00')
        self.buyer_profile.balance = Decimal('10.01')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.buyer_profile.refresh_from_db()
        self.assertEqual(str(self.buyer_profile.balance), '0.01')

    def test_F105_balance_one_cent_below(self):
        """F1-05: 余额不足（差0.01）"""
        item = self._create_item(price='10.00')
        self.buyer_profile.balance = Decimal('9.99')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('余额不足', data['error'])

    def test_F106_balance_zero(self):
        """F1-06: 余额为0"""
        item = self._create_item(price='10.00')
        self.buyer_profile.balance = Decimal('0.00')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- 等价类：用户身份 ----
    def test_F107_no_login_no_user_id(self):
        """F1-07: 未登录且未传user_id"""
        item = self._create_item()
        r = self.client.post('/trading/buy_now', {'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F108_invalid_user_id(self):
        """F1-08: 无效user_id"""
        item = self._create_item()
        r = self.client.post('/trading/buy_now', {'user_id': 99999, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- 等价类：item_id ----
    def test_F109_item_not_exist(self):
        """F1-09: item_id不存在"""
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': 99999})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F110_item_id_empty(self):
        """F1-10: item_id为空"""
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- 等价类：道具状态 ----
    def test_F111_item_off_shelf(self):
        """F1-11: 道具已下架"""
        item = self._create_item(status=Item.Status.OFF_SHELF)
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F112_item_locked(self):
        """F1-12: 道具已锁定"""
        item = self._create_item(status=Item.Status.LOCKED)
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F113_item_sold(self):
        """F1-13: 道具已售出"""
        item = self._create_item(status=Item.Status.SOLD)
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F114_stock_zero(self):
        """F1-14: 库存为0"""
        item = self._create_item(stock=0, status=Item.Status.ON_SALE)
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()
        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- 等价类：自买 ----
    def test_F115_self_buy(self):
        """F1-15: 自己买自己的道具"""
        item = self._create_item()
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()
        r = self.client.post('/trading/buy_now', {'user_id': self.seller.id, 'item_id': item.id})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('不能购买自己的道具', data['error'])

    # ---- 并发测试 ----
    def test_F116_concurrent_buy(self):
        """F1-16: 并发购买（stock=1），两个用户同时购买"""
        item = self._create_item(stock=1, price='10.00')
        buyer2 = User.objects.create_user(username='buyer2_concurrent', password='x')
        buyer2_profile, _ = UserProfile.objects.get_or_create(user=buyer2)
        buyer2_profile.balance = Decimal('100.00')
        buyer2_profile.save()
        self.buyer_profile.balance = Decimal('100.00')
        self.buyer_profile.save()

        results = []

        def do_buy(user):
            c = Client()
            r = c.post('/trading/buy_now', {'user_id': user.id, 'item_id': item.id})
            results.append(r.json())

        t1 = threading.Thread(target=do_buy, args=(self.buyer,))
        t2 = threading.Thread(target=do_buy, args=(buyer2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        ok_count = sum(1 for r in results if r.get('ok'))
        self.assertEqual(ok_count, 1, msg=f"Expected exactly 1 success, got {ok_count}: {results}")


class OrderStateFlowTests(TestCase):
    """F2~F6: 订单状态流转 —— 判定表"""

    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller_flow', password='x')
        self.buyer = User.objects.create_user(username='buyer_flow', password='x')
        self.other = User.objects.create_user(username='other_flow', password='x')
        UserProfile.objects.get_or_create(user=self.seller)
        UserProfile.objects.get_or_create(user=self.buyer)
        UserProfile.objects.get_or_create(user=self.other)

        self.item = Item.objects.create(
            name='flow_item', price='10.00', seller=self.seller,
            status=Item.Status.ON_SALE, stock=2,
        )

    # ---- F2: 创建订单 ----
    def test_F201_normal_create_order(self):
        """F2-01: 正常创建订单"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'pending_payment')

        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.status, Order.STATUS_PENDING_PAYMENT)

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.LOCKED)
        self.assertEqual(self.item.stock, 1)

    def test_F202_create_order_item_not_available(self):
        """F2-02: 道具不可售"""
        self.item.status = Item.Status.OFF_SHELF
        self.item.save()
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F203_create_order_self_buy(self):
        """F2-03: 自买"""
        r = self.client.post('/trading/order/create', {'user_id': self.seller.id, 'item_id': self.item.id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- F3: 取消订单 ----
    def test_F204_normal_cancel(self):
        """F2-04: 正常取消订单"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/order/cancel', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'cancelled')

        self.item.refresh_from_db()
        self.assertEqual(self.item.stock, 2)
        self.assertEqual(self.item.status, Item.Status.ON_SALE)

    def test_F205_cancel_by_non_buyer(self):
        """F2-05: 非买家取消订单"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/order/cancel', {'user_id': self.seller.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F206_cancel_paid_order(self):
        """F2-06: 已支付订单不可取消"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        # 模拟变为paid状态
        order = Order.objects.get(id=order_id)
        order.status = Order.STATUS_PAID
        order.save()

        r = self.client.post('/trading/order/cancel', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F207_cancel_shipped_order(self):
        """F2-07: 已发货订单不可取消"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        order = Order.objects.get(id=order_id)
        order.status = Order.STATUS_SHIPPED
        order.save()

        r = self.client.post('/trading/order/cancel', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- F4: 支付管理 ----
    def test_F208_normal_initiate_payment(self):
        """F2-08: 正常发起支付"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/payment/initiate', {
            'user_id': self.buyer.id, 'order_id': order_id, 'pay_method': 'mock'
        })
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertIn('payment_no', data)

    def test_F209_duplicate_initiate_payment(self):
        """F2-09: 重复发起支付，不重复创建"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r1 = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        no1 = r1.json()['payment_no']
        r2 = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        no2 = r2.json()['payment_no']
        self.assertEqual(no1, no2)

    def test_F210_initiate_payment_by_other(self):
        """F2-10: 非买家发起支付"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/payment/initiate', {'user_id': self.other.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F211_payment_callback_success(self):
        """F2-11: 支付回调成功"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']

        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'paid')

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_PAID)

        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.SOLD)

    def test_F212_payment_callback_failed(self):
        """F2-12: 支付回调失败"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']

        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'failed'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['pay_status'], 'failed')

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_PENDING_PAYMENT)  # 状态不变
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Item.Status.LOCKED)  # 仍锁定

    def test_F213_callback_invalid_payment_no(self):
        """F2-13: payment_no不存在"""
        r = self.client.post('/trading/payment/callback', {'payment_no': 'fake_no_12345', 'result': 'success'})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F214_duplicate_callback(self):
        """F2-14: 重复支付回调"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})

        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        data = r.json()
        self.assertFalse(data['ok'])  # 订单已不是pending_payment

    # ---- F5: 卖家发货 ----
    def test_F215_normal_ship(self):
        """F2-15: 卖家正常发货"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})

        r = self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'shipped')

    def test_F216_ship_by_non_seller(self):
        """F2-16: 非卖家发货"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})

        r = self.client.post('/trading/order/ship', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F217_ship_pending_order(self):
        """F2-17: 待支付不可发货"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    # ---- F6: 确认收货 ----
    def test_F218_normal_confirm(self):
        """F2-18: 正常确认收货，卖家收到款项"""
        initial_seller_balance = UserProfile.objects.get(user=self.seller).balance

        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})

        r = self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'completed')

        seller_profile = UserProfile.objects.get(user=self.seller)
        self.assertEqual(str(seller_profile.balance),
                         str(initial_seller_balance + Decimal('10.00')))

        log = TransactionLog.objects.filter(user=self.seller).last()
        self.assertEqual(log.type, TransactionLog.Type.CREDIT)

    def test_F219_confirm_by_non_buyer(self):
        """F2-19: 非买家确认收货"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})

        r = self.client.post('/trading/order/confirm', {'user_id': self.seller.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F220_confirm_paid_not_shipped(self):
        """F2-20: 已支付未发货不可确认"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})

        r = self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})
        data = r.json()
        self.assertFalse(data['ok'])

    def test_F221_confirm_amount_correct(self):
        """F2-21: 确认收货金额校验"""
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': self.item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']
        self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})

        seller_profile = UserProfile.objects.get(user=self.seller)
        # 如果之前有其他确认操作，balance应至少增加10
        self.assertTrue(Decimal(str(seller_profile.balance)) >= Decimal('10.00'))


class RechargeTests(TestCase):
    """F7: 账户充值 —— 等价类 + 边界值"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user_recharge', password='x')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    # ---- 等价类 ----
    def test_F701_custom_amount(self):
        """F7-01: 自定义金额充值申请（提交审核）"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '100'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['amount'], '100')
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['status_display'], '待审核')
        # 余额不变，需管理员审核后才到账
        self.profile.refresh_from_db()
        self.assertEqual(str(self.profile.balance), '0.00')

    def test_F702_specific_amount(self):
        """F7-02: 指定金额充值申请"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '50'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['amount'], '50')
        self.profile.refresh_from_db()
        self.assertEqual(str(self.profile.balance), '0.00')

    # ---- 边界值 ----
    def test_F703_recharge_zero(self):
        """F7-03: 充值0元——应被拒绝"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '0'})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('大于0', data['error'])

    def test_F704_recharge_one_cent(self):
        """F7-04: 充值0.01元（最小合法金额）"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '0.01'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['amount'], '0.01')
        self.assertEqual(data['status'], 'pending')

    def test_F705_recharge_large(self):
        """F7-05: 超大额充值——应被拒绝"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '999999.99'})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('100,000', data['error'])

    def test_F706_recharge_accumulate(self):
        """F7-06: 多次充值申请均进入审核"""
        self.profile.balance = Decimal('50.00')
        self.profile.save()
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '100'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'pending')
        # 余额不变（审核中）
        self.profile.refresh_from_db()
        self.assertEqual(str(self.profile.balance), '50.00')

    # ---- 异常等价类 ----
    def test_F707_recharge_negative(self):
        """F7-07: 负金额充值——已修复：现在会被拦截"""
        self.profile.balance = Decimal('100.00')
        self.profile.save()
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': '-100'})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('大于0', data['error'])
        # 余额不变
        self.profile.refresh_from_db()
        self.assertEqual(str(self.profile.balance), '100.00')

    def test_F708_recharge_non_numeric(self):
        """F7-08: 非数字金额——已修复：现在返回错误而非500"""
        r = self.client.post('/trading/recharge', {'user_id': self.user.id, 'amount': 'abc'})
        data = r.json()
        self.assertFalse(data['ok'])
        self.assertIn('格式不正确', data['error'])

    def test_F709_recharge_not_login(self):
        """F7-09: 未登录充值"""
        r = self.client.post('/trading/recharge', {})
        data = r.json()
        self.assertFalse(data['ok'])


class OrderListTests(TestCase):
    """订单列表接口测试"""

    def setUp(self):
        self.client = Client()
        self.buyer = User.objects.create_user(username='buyer_list', password='x')
        self.seller = User.objects.create_user(username='seller_list', password='x')
        UserProfile.objects.get_or_create(user=self.buyer)
        UserProfile.objects.get_or_create(user=self.seller)

    def test_buyer_orders_empty(self):
        """买家订单列表——无订单"""
        r = self.client.get('/trading/buyer/orders', {'user_id': self.buyer.id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['orders'], [])

    def test_buyer_orders_with_status_filter(self):
        """买家订单列表——按状态筛选"""
        item = Item.objects.create(name='test', price='5.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=1)
        Order.objects.create(buyer=self.buyer, seller=self.seller, item=item,
                             price='5.00', status=Order.STATUS_PAID)
        Order.objects.create(buyer=self.buyer, seller=self.seller, item=item,
                             price='5.00', status=Order.STATUS_PENDING_PAYMENT)

        r = self.client.get('/trading/buyer/orders', {'user_id': self.buyer.id, 'status': 'paid'})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['orders'][0]['status'], 'paid')

    def test_seller_orders(self):
        """卖家订单列表"""
        item = Item.objects.create(name='test_seller', price='5.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=1)
        Order.objects.create(buyer=self.buyer, seller=self.seller, item=item,
                             price='5.00', status=Order.STATUS_PAID)

        r = self.client.get('/trading/seller/orders', {'user_id': self.seller.id})
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['orders']), 1)


class EndToEndFlowTests(TestCase):
    """端到端业务流程测试"""

    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller_e2e', password='x')
        self.buyer = User.objects.create_user(username='buyer_e2e', password='x')
        self.buyer_profile, _ = UserProfile.objects.get_or_create(user=self.buyer)
        self.seller_profile, _ = UserProfile.objects.get_or_create(user=self.seller)

    def test_e2e_full_standard_flow(self):
        """E2E-01: 标准完整交易流程"""
        item = Item.objects.create(name='e2e_item', price='10.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=1)

        # Step 1: create_order
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': item.id})
        self.assertTrue(r.json()['ok'])
        order_id = r.json()['order_id']
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_PENDING_PAYMENT)

        # Step 2: initiate_payment
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertTrue(r.json()['ok'])
        payment_no = r.json()['payment_no']

        # Step 3: payment_callback success
        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'success'})
        self.assertTrue(r.json()['ok'])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        item.refresh_from_db()
        self.assertEqual(item.status, Item.Status.SOLD)

        # Step 4: ship_order
        r = self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        self.assertTrue(r.json()['ok'])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_SHIPPED)

        # Step 5: confirm_receipt
        r = self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertTrue(r.json()['ok'])
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)

        # 验证卖家余额
        self.seller_profile.refresh_from_db()
        self.assertEqual(str(self.seller_profile.balance), '10.00')

    def test_e2e_cancel_flow(self):
        """E2E-02: 取消订单流程"""
        item = Item.objects.create(name='cancel_item', price='5.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=2)
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': item.id})
        order_id = r.json()['order_id']

        r = self.client.post('/trading/order/cancel', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertTrue(r.json()['ok'])

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_CANCELLED)
        item.refresh_from_db()
        self.assertEqual(item.stock, 2)
        self.assertEqual(item.status, Item.Status.ON_SALE)

    def test_e2e_payment_failed_flow(self):
        """E2E-03: 支付失败流程"""
        item = Item.objects.create(name='fail_item', price='5.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=1)
        r = self.client.post('/trading/order/create', {'user_id': self.buyer.id, 'item_id': item.id})
        order_id = r.json()['order_id']
        r = self.client.post('/trading/payment/initiate', {'user_id': self.buyer.id, 'order_id': order_id})
        payment_no = r.json()['payment_no']

        r = self.client.post('/trading/payment/callback', {'payment_no': payment_no, 'result': 'failed'})
        self.assertTrue(r.json()['ok'])

        payment = Payment.objects.get(payment_no=payment_no)
        self.assertEqual(payment.pay_status, Payment.Status.FAILED)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_PENDING_PAYMENT)
        item.refresh_from_db()
        self.assertEqual(item.status, Item.Status.LOCKED)

    def test_e2e_buy_now_flow(self):
        """E2E-04: 一步购买完整流程"""
        item = Item.objects.create(name='buynow_item', price='8.00', seller=self.seller,
                                   status=Item.Status.ON_SALE, stock=1)
        self.buyer_profile.balance = Decimal('50.00')
        self.buyer_profile.save()

        r = self.client.post('/trading/buy_now', {'user_id': self.buyer.id, 'item_id': item.id})
        data = r.json()
        self.assertTrue(data['ok'])
        order_id = data['order_id']
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.STATUS_PAID)

        # 卖家发货
        self.client.post('/trading/order/ship', {'user_id': self.seller.id, 'order_id': order_id})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_SHIPPED)

        # 确认收货
        r = self.client.post('/trading/order/confirm', {'user_id': self.buyer.id, 'order_id': order_id})
        self.assertTrue(r.json()['ok'])
        self.seller_profile.refresh_from_db()
        self.assertEqual(str(self.seller_profile.balance), '8.00')
