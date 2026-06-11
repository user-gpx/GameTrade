from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Item, Category, Favorite

class ItemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='TestPass123!')
        self.buyer = User.objects.create_user(username='buyer', password='TestPass123!')
        
        self.category = Category.objects.create(name='武器', description='各种武器')
        self.item = Item.objects.create(
            name='屠龙宝刀',
            category=self.category,
            game='other',
            price=999.00,
            seller=self.seller,
            description='这是一把测试用的武器',
            status=Item.Status.ON_SALE
        )
        self.list_url = reverse('items:list')
        self.detail_url = reverse('items:detail', args=[self.item.pk])
        self.toggle_fav_url = reverse('items:toggle_favorite', args=[self.item.pk])

    def test_item_list_view(self):
        """测试道具列表展示"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '屠龙宝刀')

    def test_item_detail_view(self):
        """测试道具详情展示及浏览量增加"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '屠龙宝刀')
        self.assertContains(response, '999.00')
        
        # 验证浏览量是否增加
        self.item.refresh_from_db()
        self.assertEqual(self.item.views_count, 1)

    def test_item_search(self):
        """测试简单搜索功能"""
        # 搜索存在的关键词
        response = self.client.get(self.list_url + '?keyword=屠龙')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '屠龙宝刀')
        
        # 搜索不存在的关键词
        response_empty = self.client.get(self.list_url + '?keyword=倚天')
        self.assertEqual(response_empty.status_code, 200)
        self.assertNotContains(response_empty, '屠龙宝刀')

    def test_toggle_favorite(self):
        """测试关注/收藏功能"""
        self.client.login(username='buyer', password='TestPass123!')
        
        # 第一次请求：添加收藏
        response = self.client.get(self.toggle_fav_url)
        self.assertEqual(response.status_code, 302) # 操作后重定向回详情页
        self.assertTrue(Favorite.objects.filter(user=self.buyer, item=self.item).exists())
        
        # 第二次请求：取消收藏
        self.client.get(self.toggle_fav_url)
        self.assertFalse(Favorite.objects.filter(user=self.buyer, item=self.item).exists())

    def test_favorites_requires_login(self):
        """测试未登录用户无法操作收藏"""
        response = self.client.get(self.toggle_fav_url)
        self.assertEqual(response.status_code, 302) # 重定向到登录