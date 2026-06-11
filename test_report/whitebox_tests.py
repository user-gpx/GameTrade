"""
白盒测试脚本 (练习2)
====================
测试框架: Django TestCase + unittest.TestSuite
测试方法: 基本路径法、条件-判定覆盖、条件组合覆盖

被测代码单元:
- Unit 1: users.views.user_register (用户注册视图)
- Unit 2: items.forms.ItemForm.clean_price (道具价格验证)
- Unit 3: items.views.toggle_favorite (收藏切换视图)
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from items.models import Item, Category, Favorite
from items.forms import ItemForm
from users.forms import RegisterForm


# ============================================================
#  Unit 1: user_register 视图 — 白盒测试
#  控制流图见报告章节 4.1.2
#  V(G) = 4, 基本路径 = 4
# ============================================================

class Unit1_Register_BasicPathTests(TestCase):
    """Unit 1 基本路径法测试 — 覆盖 user_register 的 4 条独立路径"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('users:register')

    def test_path1_already_authenticated(self):
        """路径1: N1(T)→N2  — 已登录用户访问注册页 → 重定向"""
        User.objects.create_user(username='logged', password='TestPass1!')
        self.client.login(username='logged', password='TestPass1!')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_path2_post_valid(self):
        """路径2: N1(F)→N3(T)→N4→N5(T)→N6→N7→N8→N9  — POST有效 → 注册成功"""
        r = self.client.post(self.url, {
            'username': 'path2user', 'email': 'p2@t.com',
            'password1': 'Complex1!@', 'password2': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_path3_post_invalid(self):
        """路径3: N1(F)→N3(T)→N4→N5(F)→N11  — POST无效 → 返回注册页"""
        r = self.client.post(self.url, {
            'username': '', 'email': '',
            'password1': 'x', 'password2': 'x',
        })
        self.assertEqual(r.status_code, 200)

    def test_path4_get_request(self):
        """路径4: N1(F)→N3(F)→N10→N11  — GET请求 → 显示注册页"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'users/register.html')


class Unit1_Register_ConditionDecisionTests(TestCase):
    """Unit 1 条件-判定覆盖测试 — 每个条件取真/假各一次，每个判定取真/假各一次"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('users:register')

    # 判定1: request.user.is_authenticated
    def test_cd1_auth_true(self):
        """判定1-T: is_authenticated=True → redirect"""
        User.objects.create_user(username='cd1t', password='TestPass1!')
        self.client.login(username='cd1t', password='TestPass1!')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)

    def test_cd1_auth_false(self):
        """判定1-F: is_authenticated=False → 继续执行"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    # 判定2: request.method == 'POST'
    def test_cd2_method_post(self):
        """判定2-T: method='POST' → 处理表单"""
        r = self.client.post(self.url, {
            'username': 'cd2t', 'email': 'cd2t@t.com',
            'password1': 'Complex1!@', 'password2': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_cd2_method_get(self):
        """判定2-F: method='GET' → 显示空表单"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    # 判定3: form.is_valid()
    def test_cd3_form_valid(self):
        """判定3-T: form.is_valid()=True → save+login+redirect"""
        r = self.client.post(self.url, {
            'username': 'cd3t', 'email': 'cd3t@t.com',
            'password1': 'Complex1!@', 'password2': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_cd3_form_invalid(self):
        """判定3-F: form.is_valid()=False → 返回表单"""
        r = self.client.post(self.url, {
            'username': '', 'email': '',
            'password1': 'x', 'password2': 'x',
        })
        self.assertEqual(r.status_code, 200)


class Unit1_Register_ConditionCombinationTests(TestCase):
    """Unit 1 条件组合覆盖测试 — 所有条件取值组合"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('users:register')

    # 3个条件: C1=is_authenticated, C2=is_POST, C3=form_valid
    # 组合: C2和C3仅当C1=F时有意义; C3仅当C1=F且C2=T时有意义
    # 有效组合:
    def test_comb1_FFF(self):
        """组合1: auth=F, POST=F(→GET), valid=F(无意义) — GET请求"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_comb2_FTF(self):
        """组合2: auth=F, POST=T, valid=T — 注册成功"""
        r = self.client.post(self.url, {
            'username': 'comb2', 'email': 'comb2@t.com',
            'password1': 'Complex1!@', 'password2': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_comb3_FTF_invalid(self):
        """组合3: auth=F, POST=T, valid=F — 表单数据无效"""
        r = self.client.post(self.url, {
            'username': '', 'email': '', 'password1': '', 'password2': '',
        })
        self.assertEqual(r.status_code, 200)

    def test_comb4_TXX(self):
        """组合4: auth=T, (POST/valid任意) — 直接重定向"""
        User.objects.create_user(username='comb4', password='TestPass1!')
        self.client.login(username='comb4', password='TestPass1!')
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)


# ============================================================
#  Unit 2: ItemForm.clean_price — 白盒测试
#  控制流图见报告章节 4.2.2
#  V(G) = 2, 基本路径 = 2
# ============================================================

class Unit2_CleanPrice_BasicPathTests(TestCase):
    """Unit 2 基本路径法测试"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='test')

    def test_path1_valid_positive(self):
        """路径1: price is not None AND price > 0 → return price"""
        form = ItemForm({
            'name': 'test', 'category': self.cat.id,
            'game': 'other', 'price': '99.99',
            'description': 'ok',
        })
        self.assertTrue(form.is_valid())

    def test_path2_invalid_zero_or_negative(self):
        """路径2: price is not None AND price <= 0 → raise ValidationError"""
        form = ItemForm({
            'name': 'test', 'category': self.cat.id,
            'game': 'other', 'price': '0',
            'description': 'ok',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)


class Unit2_CleanPrice_ConditionDecisionTests(TestCase):
    """Unit 2 条件-判定覆盖 — 复合条件: (price is not None) AND (price <= 0)"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='test')

    # 拆分条件: C1=(price is not None), C2=(price <= 0)
    # 判定 D = C1 AND C2

    def test_cd_C1T_C2F(self):
        """C1=T, C2=F → D=F: 正价格 → 验证通过"""
        form = ItemForm({
            'name': 'ok', 'category': self.cat.id,
            'game': 'other', 'price': '1.00', 'description': 'ok',
        })
        self.assertTrue(form.is_valid())

    def test_cd_C1T_C2T(self):
        """C1=T, C2=T → D=T: price=0 → 验证失败"""
        form = ItemForm({
            'name': 'ok', 'category': self.cat.id,
            'game': 'other', 'price': '0.00', 'description': 'ok',
        })
        self.assertFalse(form.is_valid())

    def test_cd_C1T_C2T_negative(self):
        """C1=T, C2=T → D=T: 负价格 → 验证失败"""
        form = ItemForm({
            'name': 'ok', 'category': self.cat.id,
            'game': 'other', 'price': '-10.00', 'description': 'ok',
        })
        self.assertFalse(form.is_valid())

    # C1=F (price is None) — 仅当表单未提供price字段时触发
    def test_cd_C1F(self):
        """C1=F (price=None) → D=F → return price (None, 但clean后表单其他字段可能失败)"""
        form = ItemForm({
            'name': 'test', 'category': self.cat.id,
            'game': 'other', 'description': 'ok',
            # price 未提供
        })
        # price字段在ModelForm中是可选的(blank=False但form未提供), 这取决于字段定义
        is_valid = form.is_valid()
        if not is_valid:
            self.assertIn('price', form.errors)


class Unit2_CleanPrice_ConditionCombinationTests(TestCase):
    """Unit 2 条件组合覆盖 — 所有 C1×C2 组合"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='test')

    def test_comb_CC1T_C2T_zero(self):
        """组合1: C1=T, C2=T (price=0) → 验证失败"""
        form = ItemForm({
            'name': 'x', 'category': self.cat.id,
            'game': 'other', 'price': '0.00', 'description': 'x',
        })
        self.assertFalse(form.is_valid())

    def test_comb_CC1T_C2T_negative(self):
        """组合2: C1=T, C2=T (price<0) → 验证失败"""
        form = ItemForm({
            'name': 'x', 'category': self.cat.id,
            'game': 'other', 'price': '-5.50', 'description': 'x',
        })
        self.assertFalse(form.is_valid())

    def test_comb_CC1T_C2F(self):
        """组合3: C1=T, C2=F (price>0) → 验证通过"""
        form = ItemForm({
            'name': 'x', 'category': self.cat.id,
            'game': 'other', 'price': '88.88', 'description': 'x',
        })
        self.assertTrue(form.is_valid())

    def test_comb_CC1F_C2_any(self):
        """组合4: C1=F (price=None) → 验证取决于是否为必填"""
        form = ItemForm({
            'name': 'x', 'category': self.cat.id,
            'game': 'other', 'description': 'x',
        })
        # price 不是必填(ModelForm不强制)
        is_valid = form.is_valid()
        # 验证 clean_price 不因 price=None 而崩溃
        print(f"  price=None → is_valid={is_valid}, errors={form.errors if not is_valid else 'none'}")


# ============================================================
#  Unit 3: toggle_favorite 视图 — 白盒测试
#  控制流图见报告章节 4.3.2
#  V(G) = 3, 基本路径 = 3
# ============================================================

class Unit3_ToggleFav_BasicPathTests(TestCase):
    """Unit 3 基本路径法测试"""

    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user(username='favseller', password='TestPass1!')
        cls.buyer = User.objects.create_user(username='favbuyer', password='TestPass1!')
        cls.cat = Category.objects.create(name='test')
        cls.item = Item.objects.create(
            name='favtest', category=cls.cat, game='other',
            price=1.00, seller=cls.seller, status=Item.Status.ON_SALE,
        )

    def setUp(self):
        self.client = Client()

    def test_path1_add_favorite_ajax(self):
        """路径1: N1→N2→N3(F)→N7→N8→N9(T)→N10 [add+AJAX]"""
        self.client.login(username='favbuyer', password='TestPass1!')
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['is_favorited'])

    def test_path2_remove_favorite_ajax(self):
        """路径2: N1→N2→N3(T)→N4→N5→N6→N9(T)→N10 [remove+AJAX]"""
        self.client.login(username='favbuyer', password='TestPass1!')
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data['is_favorited'])

    def test_path3_non_ajax_redirect(self):
        """路径3: N1→N2→N3()→N9(F)→N11→N12 [普通请求→重定向]"""
        self.client.login(username='favbuyer', password='TestPass1!')
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)


class Unit3_ToggleFav_ConditionDecisionTests(TestCase):
    """Unit 3 条件-判定覆盖"""

    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user(username='cdseller', password='TestPass1!')
        cls.buyer = User.objects.create_user(username='cdbuyer', password='TestPass1!')
        cls.cat = Category.objects.create(name='test')
        cls.item = Item.objects.create(
            name='cdtest', category=cls.cat, game='other',
            price=1.00, seller=cls.seller, status=Item.Status.ON_SALE,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='cdbuyer', password='TestPass1!')

    # 判定1: not created (即 created==False, 表示已存在)
    def test_cd_created_true(self):
        """判定1-F: created=True (新创建) → 收藏成功"""
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertTrue(r.json()['is_favorited'])

    def test_cd_created_false(self):
        """判定1-T: created=False (已存在) → 取消收藏"""
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertFalse(r.json()['is_favorited'])

    # 判定2: request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    def test_cd_ajax_true(self):
        """判定2-T: AJAX请求 → 返回JSON"""
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/json')

    def test_cd_ajax_false(self):
        """判定2-F: 普通请求 → 重定向"""
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)


class Unit3_ToggleFav_ConditionCombinationTests(TestCase):
    """Unit 3 条件组合覆盖 — C1=(not created), C2=(AJAX)"""

    @classmethod
    def setUpTestData(cls):
        cls.seller = User.objects.create_user(username='ccfavs', password='TestPass1!')
        cls.buyer = User.objects.create_user(username='ccfavb', password='TestPass1!')
        cls.cat = Category.objects.create(name='test')
        cls.item = Item.objects.create(
            name='cctest', category=cls.cat, game='other',
            price=1.00, seller=cls.seller, status=Item.Status.ON_SALE,
        )

    def test_comb_created_true_ajax(self):
        """组合1: created=True(新添加), AJAX=True → JSON{is_favorited:True}"""
        self.client.login(username='ccfavb', password='TestPass1!')
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = r.json()
        self.assertTrue(data['is_favorited'])

    def test_comb_created_true_non_ajax(self):
        """组合2: created=True, AJAX=False → 302重定向"""
        self.client.login(username='ccfavb', password='TestPass1!')
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)

    def test_comb_created_false_ajax(self):
        """组合3: created=False(已存在,取消), AJAX=True → JSON{is_favorited:False}"""
        self.client.login(username='ccfavb', password='TestPass1!')
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = r.json()
        self.assertFalse(data['is_favorited'])

    def test_comb_created_false_non_ajax(self):
        """组合4: created=False, AJAX=False → 302重定向"""
        self.client.login(username='ccfavb', password='TestPass1!')
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)


# ============================================================
#  TestSuite 组合
# ============================================================

def build_whitebox_suite():
    """构建白盒测试套件，按单元和方法组织"""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Unit 1: user_register
    suite.addTest(loader.loadTestsFromTestCase(Unit1_Register_BasicPathTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit1_Register_ConditionDecisionTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit1_Register_ConditionCombinationTests))

    # Unit 2: clean_price
    suite.addTest(loader.loadTestsFromTestCase(Unit2_CleanPrice_BasicPathTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit2_CleanPrice_ConditionDecisionTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit2_CleanPrice_ConditionCombinationTests))

    # Unit 3: toggle_favorite
    suite.addTest(loader.loadTestsFromTestCase(Unit3_ToggleFav_BasicPathTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit3_ToggleFav_ConditionDecisionTests))
    suite.addTest(loader.loadTestsFromTestCase(Unit3_ToggleFav_ConditionCombinationTests))

    return suite


# ============================================================
#  独立运行入口
# ============================================================
if __name__ == '__main__':
    import sys
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    # Django setup
    import django
    django.setup()

    runner = unittest.TextTestRunner(verbosity=2)
    suite = build_whitebox_suite()
    result = runner.run(suite)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    print(f"\n{'='*60}")
    print(f"  白盒测试汇总: {total} total, {total-failures-errors} pass, "
          f"{failures} fail, {errors} error")
    print(f"{'='*60}")
