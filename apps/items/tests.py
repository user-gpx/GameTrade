"""
Items 模块测试套件

测试方法论:
- 白盒测试: 语句覆盖、条件覆盖、基本路径覆盖
- 黑盒测试: 等价类划分、边界值分析、判定表、场景法、正交实验法
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Item, Category, Favorite
from .forms import ItemForm, ItemSearchForm


# ============================================================
#  白盒测试 — 语句覆盖、条件覆盖、基本路径覆盖
# ============================================================

class ItemViewsWhiteBoxTests(TestCase):
    """道具视图白盒测试 — 覆盖每个分支/路径"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='武器', description='各类武器')
        cls.seller = User.objects.create_user(username='itemseller', password='TestPass1!')
        cls.buyer = User.objects.create_user(username='itembuyer', password='TestPass1!')
        cls.item = Item.objects.create(
            name='屠龙宝刀', category=cls.cat, game='other',
            price=999.00, seller=cls.seller,
            description='一把传说中的宝刀', status=Item.Status.ON_SALE, stock=5,
        )
        cls.item2 = Item.objects.create(
            name='倚天剑', category=cls.cat, game='other',
            price=299.00, seller=cls.seller,
            description='剑中之王', status=Item.Status.ON_SALE, stock=3,
        )

    def setUp(self):
        self.client = Client()

    # ---------- item_list 视图 ----------

    def test_list_no_params(self):
        """语句覆盖: 无参数 → 返回在售道具列表"""
        r = self.client.get(reverse('items:list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '屠龙宝刀')
        self.assertContains(r, '倚天剑')

    def test_list_keyword_search_match(self):
        """条件覆盖: 关键词匹配 → 返回筛选结果"""
        r = self.client.get(reverse('items:list') + '?keyword=屠龙')
        self.assertContains(r, '屠龙宝刀')
        self.assertNotContains(r, '倚天剑')

    def test_list_keyword_no_match(self):
        """条件覆盖: 关键词无匹配 → 空列表"""
        r = self.client.get(reverse('items:list') + '?keyword=不存在的道具XYZ')
        self.assertEqual(r.status_code, 200)

    def test_list_game_filter(self):
        """条件覆盖: 按游戏筛选"""
        r = self.client.get(reverse('items:list') + '?game=other')
        self.assertContains(r, '倚天剑')
        self.assertContains(r, '屠龙宝刀')
        # 筛选 lol 应该没有结果
        r = self.client.get(reverse('items:list') + '?game=lol')
        self.assertNotContains(r, '屠龙宝刀')
        self.assertNotContains(r, '倚天剑')

    def test_list_category_filter(self):
        """条件覆盖: 按分类筛选"""
        r = self.client.get(reverse('items:list') + f'?category={self.cat.id}')
        self.assertEqual(r.status_code, 200)

    def test_list_price_filter_min(self):
        """条件覆盖: 最低价筛选"""
        r = self.client.get(reverse('items:list') + '?min_price=500')
        self.assertContains(r, '屠龙宝刀')
        self.assertNotContains(r, '倚天剑')

    def test_list_price_filter_max(self):
        """条件覆盖: 最高价筛选"""
        r = self.client.get(reverse('items:list') + '?max_price=500')
        self.assertContains(r, '倚天剑')
        self.assertNotContains(r, '屠龙宝刀')

    def test_list_sort_by_price_asc(self):
        """条件覆盖: 按价格升序"""
        r = self.client.get(reverse('items:list') + '?sort=price')
        content = r.content.decode('utf-8')
        idx_yitian = content.index('倚天剑')
        idx_tulong = content.index('屠龙宝刀')
        self.assertLess(idx_yitian, idx_tulong)

    def test_list_sort_by_price_desc(self):
        """条件覆盖: 按价格降序"""
        r = self.client.get(reverse('items:list') + '?sort=-price')
        content = r.content.decode('utf-8')
        idx_tulong = content.index('屠龙宝刀')
        idx_yitian = content.index('倚天剑')
        self.assertLess(idx_tulong, idx_yitian)

    def test_list_sort_by_views(self):
        """条件覆盖: 按浏览量排序"""
        r = self.client.get(reverse('items:list') + '?sort=-views_count')
        self.assertEqual(r.status_code, 200)

    def test_list_combined_filters(self):
        """语句覆盖: 多条件组合"""
        r = self.client.get(reverse('items:list') +
                            '?keyword=剑&min_price=100&max_price=500&sort=price')
        self.assertContains(r, '倚天剑')

    def test_list_no_sold_items(self):
        """条件覆盖: 不显示已售道具"""
        self.item.status = Item.Status.SOLD
        self.item.save()
        r = self.client.get(reverse('items:list'))
        self.assertNotContains(r, '屠龙宝刀')
        self.item.status = Item.Status.ON_SALE
        self.item.save()

    def test_list_no_off_shelf_items(self):
        """条件覆盖: 不显示已下架道具"""
        self.item.status = Item.Status.OFF_SHELF
        self.item.save()
        r = self.client.get(reverse('items:list'))
        self.assertNotContains(r, '屠龙宝刀')
        self.item.status = Item.Status.ON_SALE
        self.item.save()

    # ---------- item_detail 视图 ----------

    def test_detail_existing_item(self):
        """语句覆盖: 查看存在的道具"""
        r = self.client.get(reverse('items:detail', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)

    def test_detail_increments_views(self):
        """语句覆盖: 浏览量递增"""
        old_views = self.item.views_count
        self.client.get(reverse('items:detail', args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.views_count, old_views + 1)

    def test_detail_nonexistent_item_404(self):
        """条件覆盖: 不存在的道具 → 404"""
        r = self.client.get(reverse('items:detail', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_detail_shows_related_items(self):
        """语句覆盖: 详情页展示相关道具"""
        r = self.client.get(reverse('items:detail', args=[self.item.pk]))
        self.assertContains(r, '倚天剑')

    # ---------- item_create 视图 ----------

    def test_create_get_requires_login(self):
        """条件覆盖: 未登录 → 302"""
        r = self.client.get(reverse('items:create'))
        self.assertEqual(r.status_code, 302)

    def test_create_get_renders_form(self):
        """语句覆盖: GET → 渲染创建表单"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.get(reverse('items:create'))
        self.assertEqual(r.status_code, 200)

    def test_create_post_valid_item(self):
        """语句覆盖: POST 有效 → 创建道具 → 重定向"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:create'), {
            'name': '新道具', 'category': self.cat.id,
            'game': 'lol', 'price': '100.00', 'description': '新建的道具',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Item.objects.filter(name='新道具').exists())

    def test_create_post_zero_price(self):
        """条件覆盖: 价格为0 → 验证失败"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:create'), {
            'name': '零价道具', 'category': self.cat.id,
            'game': 'other', 'price': '0.00', 'description': '无效',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Item.objects.filter(name='零价道具').exists())

    def test_create_post_negative_price(self):
        """条件覆盖: 价格为负 → 验证失败"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:create'), {
            'name': '负价道具', 'category': self.cat.id,
            'game': 'other', 'price': '-10.00', 'description': '无效',
        })
        self.assertEqual(r.status_code, 200)

    def test_create_post_missing_required(self):
        """条件覆盖: 缺少必填字段 → 验证失败"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:create'), {
            'name': '', 'price': '50.00',
        })
        self.assertEqual(r.status_code, 200)

    # ---------- item_edit 视图 ----------

    def test_edit_get_renders_form(self):
        """语句覆盖: GET → 渲染编辑表单"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.get(reverse('items:edit', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)

    def test_edit_post_valid_updates(self):
        """语句覆盖: POST 有效 → 更新道具"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:edit', args=[self.item.pk]), {
            'name': '屠龙宝刀(升级版)', 'category': self.cat.id,
            'game': 'other', 'price': '1299.00',
            'description': '升级后的宝刀',
        })
        self.assertEqual(r.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, '屠龙宝刀(升级版)')
        self.item.name = '屠龙宝刀'  # 恢复
        self.item.save()

    def test_edit_not_owner_forbidden(self):
        """条件覆盖: 非发布者编辑 → 404（get_object_or_404 过滤了 seller）"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.get(reverse('items:edit', args=[self.item.pk]))
        self.assertEqual(r.status_code, 404)

    def test_edit_not_authenticated(self):
        """条件覆盖: 未登录 → 302"""
        r = self.client.get(reverse('items:edit', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)

    # ---------- item_delete 视图 ----------

    def test_delete_get_confirm_page(self):
        """语句覆盖: GET → 渲染确认删除页面"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.get(reverse('items:delete', args=[self.item.pk]))
        self.assertEqual(r.status_code, 200)

    def test_delete_post_soft_delete(self):
        """语句覆盖: POST → 软删除（状态改为 off_shelf）"""
        temp_item = Item.objects.create(
            name='临时道具', category=self.cat, game='other',
            price=1.00, seller=self.seller, status=Item.Status.ON_SALE, stock=1,
        )
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.post(reverse('items:delete', args=[temp_item.pk]))
        self.assertEqual(r.status_code, 302)
        temp_item.refresh_from_db()
        self.assertEqual(temp_item.status, Item.Status.OFF_SHELF)

    def test_delete_not_owner(self):
        """条件覆盖: 非发布者删除 → 404"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.post(reverse('items:delete', args=[self.item.pk]))
        self.assertEqual(r.status_code, 404)

    # ---------- toggle_favorite 视图 ----------

    def test_fav_add_first_time(self):
        """语句覆盖: 首次收藏 → 创建 Favorite"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            Favorite.objects.filter(user__username='itembuyer',
                                    item=self.item).exists()
        )

    def test_fav_remove_second_time(self):
        """条件覆盖: 已收藏 → 取消收藏"""
        self.client.login(username='itembuyer', password='TestPass1!')
        # 先收藏
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(
            Favorite.objects.filter(user__username='itembuyer',
                                    item=self.item).exists()
        )

    def test_fav_ajax_request(self):
        """条件覆盖: AJAX 请求 → 返回 JSON"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.get(
            reverse('items:toggle_favorite', args=[self.item.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('is_favorited', data)

    def test_fav_not_authenticated(self):
        """条件覆盖: 未登录 → 302"""
        r = self.client.get(reverse('items:toggle_favorite', args=[self.item.pk]))
        self.assertEqual(r.status_code, 302)

    # ---------- favorites_list 视图 ----------

    def test_favorites_list_with_data(self):
        """语句覆盖: 有收藏 → 展示列表"""
        self.client.login(username='itembuyer', password='TestPass1!')
        Favorite.objects.create(user=self.buyer, item=self.item)
        r = self.client.get(reverse('items:favorites'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '屠龙宝刀')

    def test_favorites_list_empty(self):
        """条件覆盖: 无收藏 → 空列表"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.get(reverse('items:favorites'))
        self.assertEqual(r.status_code, 200)

    def test_favorites_list_not_authenticated(self):
        """条件覆盖: 未登录 → 302"""
        r = self.client.get(reverse('items:favorites'))
        self.assertEqual(r.status_code, 302)

    # ---------- my_items 视图 ----------

    def test_my_items_with_data(self):
        """语句覆盖: 有道具 → 展示列表"""
        self.client.login(username='itemseller', password='TestPass1!')
        r = self.client.get(reverse('items:my_items'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '屠龙宝刀')
        self.assertContains(r, '倚天剑')

    def test_my_items_empty(self):
        """条件覆盖: 无道具 → 空列表"""
        self.client.login(username='itembuyer', password='TestPass1!')
        r = self.client.get(reverse('items:my_items'))
        self.assertEqual(r.status_code, 200)

    def test_my_items_not_authenticated(self):
        """条件覆盖: 未登录 → 302"""
        r = self.client.get(reverse('items:my_items'))
        self.assertEqual(r.status_code, 302)


class ItemFormsWhiteBoxTests(TestCase):
    """道具表单白盒测试"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='武器')

    def test_item_form_valid_data(self):
        """语句覆盖: 所有有效字段"""
        form = ItemForm({
            'name': '测试道具', 'category': self.cat.id,
            'game': 'lol', 'price': '99.99',
            'description': '测试描述',
        })
        self.assertTrue(form.is_valid())

    def test_item_form_blank_name(self):
        """条件覆盖: 名称为空"""
        form = ItemForm({
            'name': '', 'category': self.cat.id,
            'game': 'other', 'price': '10.00',
            'description': '无名称',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_item_form_zero_price(self):
        """条件覆盖: clean_price — price=0"""
        form = ItemForm({
            'name': '零价', 'category': self.cat.id,
            'game': 'other', 'price': '0.00',
            'description': '价格为零',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_item_form_negative_price(self):
        """条件覆盖: clean_price — price<0"""
        form = ItemForm({
            'name': '负价', 'category': self.cat.id,
            'game': 'other', 'price': '-5.00',
            'description': '负价格',
        })
        self.assertFalse(form.is_valid())

    def test_item_form_decimal_price(self):
        """语句覆盖: 小数价格"""
        form = ItemForm({
            'name': '小数价', 'category': self.cat.id,
            'game': 'other', 'price': '0.99',
            'description': '小数价格',
        })
        self.assertTrue(form.is_valid())

    def test_search_form_all_fields(self):
        """语句覆盖: 搜索表单所有字段"""
        form = ItemSearchForm({
            'keyword': '宝刀',
            'game': 'other',
            'min_price': '10',
            'max_price': '1000',
            'sort': '-price',
        })
        self.assertTrue(form.is_valid())

    def test_search_form_empty(self):
        """语句覆盖: 搜索表单全空"""
        form = ItemSearchForm({})
        self.assertTrue(form.is_valid())

    def test_search_form_keyword_only(self):
        """条件覆盖: 仅关键词"""
        form = ItemSearchForm({'keyword': 'test'})
        self.assertTrue(form.is_valid())


class ItemModelsWhiteBoxTests(TestCase):
    """道具模型白盒测试"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='modeltest', password='TestPass1!')
        cls.cat = Category.objects.create(name='防具', description='各种防具',
                                           icon='fas fa-shield')

    def test_category_str(self):
        """语句覆盖: Category.__str__"""
        self.assertEqual(str(self.cat), '防具')

    def test_item_str(self):
        """语句覆盖: Item.__str__"""
        item = Item.objects.create(
            name='测试甲', category=self.cat, game='wow',
            price=100.00, seller=self.user, status=Item.Status.ON_SALE,
        )
        self.assertEqual(str(item), '测试甲')

    def test_get_status_display_class_available(self):
        """条件覆盖: available → bg-success"""
        item = Item.objects.create(
            name='可用', category=self.cat, game='other',
            price=1.00, seller=self.user, status=Item.Status.ON_SALE,
        )
        self.assertEqual(item.get_status_display_class(), 'bg-success')

    def test_get_status_display_class_sold(self):
        """条件覆盖: sold → bg-secondary"""
        item = Item.objects.create(
            name='已售', category=self.cat, game='other',
            price=1.00, seller=self.user, status=Item.Status.SOLD,
        )
        self.assertEqual(item.get_status_display_class(), 'bg-secondary')

    def test_get_status_display_class_off_shelf(self):
        """条件覆盖: off_shelf → bg-warning"""
        item = Item.objects.create(
            name='下架', category=self.cat, game='other',
            price=1.00, seller=self.user,
            status=Item.Status.OFF_SHELF,
        )
        self.assertEqual(item.get_status_display_class(), 'bg-warning')

    def test_favorite_str(self):
        """语句覆盖: Favorite.__str__"""
        item = Item.objects.create(
            name='收藏品', category=self.cat, game='other',
            price=1.00, seller=self.user, status=Item.Status.ON_SALE,
        )
        fav = Favorite.objects.create(user=self.user, item=item)
        self.assertIn(self.user.username, str(fav))
        self.assertIn(item.name, str(fav))


# ============================================================
#  黑盒测试 — 等价类划分、边界值分析、判定表、场景法、正交实验法
# ============================================================

class ItemBlackBoxEquivalenceClass(TestCase):
    """等价类划分测试 — 道具相关输入"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='消耗品')
        cls.seller = User.objects.create_user(username='eqseller', password='TestPass1!')

    def setUp(self):
        self.client = Client()
        self.client.login(username='eqseller', password='TestPass1!')

    # ---- 道具名称等价类 ----

    def test_name_valid_short(self):
        """有效等价类: 短名称"""
        r = self.client.post(reverse('items:create'), {
            'name': '药', 'category': self.cat.id, 'game': 'other',
            'price': '5.00', 'description': '短名',
        })
        self.assertEqual(r.status_code, 302)

    def test_name_valid_unicode(self):
        """有效等价类: 含特殊字符的名称"""
        r = self.client.post(reverse('items:create'), {
            'name': '★传奇装备☆', 'category': self.cat.id, 'game': 'other',
            'price': '500.00', 'description': '特殊字符',
        })
        self.assertEqual(r.status_code, 302)

    def test_name_invalid_empty(self):
        """无效等价类: 空名称"""
        r = self.client.post(reverse('items:create'), {
            'name': '', 'category': self.cat.id, 'game': 'other',
            'price': '10.00', 'description': '空名',
        })
        self.assertEqual(r.status_code, 200)

    # ---- 价格等价类 ----

    def test_price_valid_positive(self):
        """有效等价类: 正价格"""
        r = self.client.post(reverse('items:create'), {
            'name': '正价', 'category': self.cat.id, 'game': 'other',
            'price': '99.99', 'description': '正价格',
        })
        self.assertEqual(r.status_code, 302)

    def test_price_invalid_zero(self):
        """无效等价类: 零价格"""
        r = self.client.post(reverse('items:create'), {
            'name': '零价', 'category': self.cat.id, 'game': 'other',
            'price': '0', 'description': '零价格',
        })
        self.assertEqual(r.status_code, 200)

    def test_price_invalid_negative(self):
        """无效等价类: 负价格"""
        r = self.client.post(reverse('items:create'), {
            'name': '负价', 'category': self.cat.id, 'game': 'other',
            'price': '-1', 'description': '负数',
        })
        self.assertEqual(r.status_code, 200)

    # ---- 游戏分类等价类 ----

    def test_game_valid_each_choice(self):
        """有效等价类: 每个游戏选项"""
        valid_games = ['lol', 'csgo', 'dota2', 'genshin', 'pubg', 'valorant', 'wow', 'other']
        for game in valid_games:
            Item.objects.create(
                name=f'道具-{game}', category=self.cat, game=game,
                price=10.00, seller=self.seller, status=Item.Status.ON_SALE,
            )


class ItemBlackBoxBoundaryValue(TestCase):
    """边界值分析测试 — 道具输入边界"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='边界测试')
        cls.seller = User.objects.create_user(username='bvseller', password='TestPass1!')

    def setUp(self):
        self.client = Client()
        self.client.login(username='bvseller', password='TestPass1!')

    def test_price_boundary_min_001(self):
        """边界值: 价格 = 0.01（最小正价格）"""
        r = self.client.post(reverse('items:create'), {
            'name': '最小价', 'category': self.cat.id, 'game': 'other',
            'price': '0.01', 'description': '最小正价',
        })
        self.assertEqual(r.status_code, 302)

    def test_price_boundary_zero(self):
        """边界值: 价格 = 0.00"""
        r = self.client.post(reverse('items:create'), {
            'name': '边界零', 'category': self.cat.id, 'game': 'other',
            'price': '0.00', 'description': '价格为零',
        })
        self.assertEqual(r.status_code, 200)

    def test_price_boundary_neg_001(self):
        """边界值: 价格 = -0.01"""
        r = self.client.post(reverse('items:create'), {
            'name': '负边界', 'category': self.cat.id, 'game': 'other',
            'price': '-0.01', 'description': '负数',
        })
        self.assertEqual(r.status_code, 200)

    def test_price_boundary_large(self):
        """边界值: 价格 = 99999999.99（极大值）"""
        r = self.client.post(reverse('items:create'), {
            'name': '天价', 'category': self.cat.id, 'game': 'other',
            'price': '99999999.99', 'description': '天价',
        })
        self.assertEqual(r.status_code, 302)

    def test_name_boundary_max_length(self):
        """边界值: 名称 200 字符"""
        long_name = '道' * 200
        r = self.client.post(reverse('items:create'), {
            'name': long_name, 'category': self.cat.id, 'game': 'other',
            'price': '10.00', 'description': '长名称',
        })
        self.assertEqual(r.status_code, 302)

    def test_page_boundary_page_1(self):
        """边界值: 页码 = 1（首页）"""
        r = self.client.get(reverse('items:list') + '?page=1')
        self.assertEqual(r.status_code, 200)

    def test_page_boundary_negative(self):
        """边界值: 页码为负数 → Django 返回最后一页或空"""
        r = self.client.get(reverse('items:list') + '?page=-1')
        self.assertEqual(r.status_code, 200)

    def test_page_boundary_very_large(self):
        """边界值: 超大的页码"""
        r = self.client.get(reverse('items:list') + '?page=999999')
        self.assertEqual(r.status_code, 200)


class ItemBlackBoxDecisionTable(TestCase):
    """判定表测试 — 道具操作多条件组合"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='判定测试')
        cls.owner = User.objects.create_user(username='dtowner', password='TestPass1!')
        cls.other = User.objects.create_user(username='dtother', password='TestPass1!')

    def test_owner_available_can_edit(self):
        """判定: (available + 所有者) → 可以编辑"""
        item = Item.objects.create(
            name='可编辑', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.ON_SALE,
        )
        self.client.login(username='dtowner', password='TestPass1!')
        r = self.client.get(reverse('items:edit', args=[item.pk]))
        self.assertEqual(r.status_code, 200)

    def test_other_available_cannot_edit(self):
        """判定: (available + 非所有者) → 不可以编辑"""
        item = Item.objects.create(
            name='不可编辑', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.ON_SALE,
        )
        self.client.login(username='dtother', password='TestPass1!')
        r = self.client.get(reverse('items:edit', args=[item.pk]))
        self.assertEqual(r.status_code, 404)

    def test_not_logged_in_cannot_edit(self):
        """判定: (未登录) → 重定向"""
        item = Item.objects.create(
            name='游客不可编辑', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.ON_SALE,
        )
        r = self.client.get(reverse('items:edit', args=[item.pk]))
        self.assertEqual(r.status_code, 302)

    def test_favorite_toggle_logic(self):
        """判定: (已收藏, 已登录) → 取消; (未收藏, 已登录) → 添加"""
        item = Item.objects.create(
            name='收藏切换', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.ON_SALE,
        )
        self.client.login(username='dtother', password='TestPass1!')

        # 未收藏 → 添加
        self.client.get(reverse('items:toggle_favorite', args=[item.pk]))
        self.assertTrue(Favorite.objects.filter(user=self.other, item=item).exists())

        # 已收藏 → 取消
        self.client.get(reverse('items:toggle_favorite', args=[item.pk]))
        self.assertFalse(Favorite.objects.filter(user=self.other, item=item).exists())

    def test_status_actions_table(self):
        """判定: status + 用户角色 → 允许/禁止的操作"""
        # 创建不同状态的道具
        available = Item.objects.create(
            name='在售', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.ON_SALE,
        )
        sold = Item.objects.create(
            name='已售', category=self.cat, game='other', price=10.00,
            seller=self.owner, status=Item.Status.SOLD,
        )

        # 在售道具在列表中可见
        r = self.client.get(reverse('items:list'))
        self.assertContains(r, '在售')
        # 已售道具不再显示在列表
        self.assertNotContains(r, '已售')


class ItemBlackBoxScenarioTests(TestCase):
    """场景法测试 — 完整道具生命周期"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='场景测试')
        Item.objects.create(
            name='参考道具', category=cls.cat, game='other', price=10.00,
            seller=User.objects.create_user(username='refseller', password='TestPass1!'),
            status=Item.Status.ON_SALE,
        )

    def setUp(self):
        self.client = Client()

    def test_complete_item_lifecycle(self):
        """场景: 发布 → 浏览 → 查看详情 → 编辑 → 收藏 → 取消收藏 → 下架"""
        # 先创建卖家账户
        seller_username = 'lifecycle_seller'
        User.objects.create_user(username=seller_username, password='LifeCycle1!')
        self.client.login(username=seller_username, password='LifeCycle1!')

        # Step 1: 发布道具
        r = self.client.post(reverse('items:create'), {
            'name': '生命周周期道具', 'category': self.cat.id,
            'game': 'lol', 'price': '88.00', 'description': '全生命周期测试',
        })
        self.assertEqual(r.status_code, 302)
        item = Item.objects.get(name='生命周周期道具')
        self.assertEqual(item.status, Item.Status.ON_SALE)

        # Step 2: 在列表中可见
        r = self.client.get(reverse('items:list'))
        self.assertContains(r, '生命周周期道具')

        # Step 3: 查看详情（浏览量+1）
        r = self.client.get(reverse('items:detail', args=[item.pk]))
        self.assertEqual(r.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.views_count, 1)

        # Step 4: 编辑道具
        r = self.client.post(reverse('items:edit', args=[item.pk]), {
            'name': '生命周周期道具v2', 'category': self.cat.id,
            'game': 'lol', 'price': '128.00',
            'description': '升级版描述',
        })
        self.assertEqual(r.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.price, 128.00)

        # Step 5: 另一个用户登录收藏
        User.objects.create_user(username='lifecycle_liker', password='TestPass1!')
        self.client.login(username='lifecycle_liker', password='TestPass1!')
        r = self.client.get(reverse('items:toggle_favorite', args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Favorite.objects.filter(item=item).exists())

        # 查看收藏列表
        r = self.client.get(reverse('items:favorites'))
        self.assertContains(r, '生命周周期道具v2')

        # Step 6: 取消收藏
        r = self.client.get(reverse('items:toggle_favorite', args=[item.pk]))
        self.assertFalse(Favorite.objects.filter(item=item).exists())

        # Step 7: 卖家登录，下架道具
        self.client.login(username=seller_username, password='LifeCycle1!')
        r = self.client.post(reverse('items:delete', args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, Item.Status.OFF_SHELF)

        # 下架后在列表中不可见
        r = self.client.get(reverse('items:list'))
        self.assertNotContains(r, '生命周周期道具v2')

    def test_search_scenario(self):
        """场景: 多条件搜索组合"""
        # 创建搜索目标
        seller = User.objects.get(username='refseller')
        Item.objects.create(
            name='极品攻速手套', category=self.cat, game='pubg',
            price=350.00, seller=seller, description='攻速+20%',
            status=Item.Status.ON_SALE,
        )
        # 关键词搜索
        r = self.client.get(reverse('items:list') + '?keyword=手套')
        self.assertContains(r, '极品攻速手套')
        # 价格范围搜索
        r = self.client.get(reverse('items:list') + '?min_price=300&max_price=400')
        self.assertContains(r, '极品攻速手套')
        # 游戏筛选
        r = self.client.get(reverse('items:list') + '?game=pubg')
        self.assertContains(r, '极品攻速手套')


class ItemBlackBoxOrthogonalExperiment(TestCase):
    """正交实验法测试 — 多因子搜索组合"""

    @classmethod
    def setUpTestData(cls):
        cls.cat1 = Category.objects.create(name='武器')
        cls.cat2 = Category.objects.create(name='防具')
        seller = User.objects.create_user(username='ortho', password='TestPass1!')
        # 因子A: game (lol, pubg)
        # 因子B: price_level (低<100, 中100-500, 高>500)
        # 因子C: category (武器, 防具)
        Item.objects.create(name='LOL便宜武器', category=cls.cat1, game='lol',
                            price=50.00, seller=seller, status=Item.Status.ON_SALE)
        Item.objects.create(name='LOL中等防具', category=cls.cat2, game='lol',
                            price=300.00, seller=seller, status=Item.Status.ON_SALE)
        Item.objects.create(name='PUBG高级武器', category=cls.cat1, game='pubg',
                            price=800.00, seller=seller, status=Item.Status.ON_SALE)

    def test_orthogonal_game_lol_price_low(self):
        """正交组合: game=lol + min=0 + max=100"""
        r = self.client.get(
            reverse('items:list') + '?game=lol&min_price=0&max_price=100'
        )
        self.assertContains(r, 'LOL便宜武器')

    def test_orthogonal_game_pubg_price_high(self):
        """正交组合: game=pubg + min=600 + max=1000"""
        r = self.client.get(
            reverse('items:list') + '?game=pubg&min_price=600&max_price=1000'
        )
        self.assertContains(r, 'PUBG高级武器')

    def test_orthogonal_category_weapon_game_all(self):
        """正交组合: category=武器 无游戏限制"""
        r = self.client.get(
            reverse('items:list') + f'?category={self.cat1.id}'
        )
        self.assertContains(r, 'LOL便宜武器')
        self.assertContains(r, 'PUBG高级武器')

    def test_orthogonal_keyword_game_price(self):
        """正交组合: keyword + game + price range"""
        r = self.client.get(
            reverse('items:list') + '?keyword=武器&game=pubg&min_price=500'
        )
        self.assertContains(r, 'PUBG高级武器')

    def test_orthogonal_sort_by_price_with_category(self):
        """正交组合: 排序+分类+价格范围"""
        r = self.client.get(
            reverse('items:list') +
            f'?sort=price&category={self.cat1.id}&max_price=900'
        )
        self.assertEqual(r.status_code, 200)
