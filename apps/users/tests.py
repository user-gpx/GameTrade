from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class UserAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')
        self.logout_url = reverse('users:logout')
        
    def test_user_registration(self):
        """测试用户注册功能"""
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        # 注册成功后应重定向到首页
        self.assertEqual(response.status_code, 302) 
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # 验证信号是否成功触发，创建了 UserProfile
        user = User.objects.get(username='testuser')
        self.assertTrue(hasattr(user, 'profile'))

    def test_user_login(self):
        """测试用户登录功能"""
        User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        # 登录成功后重定向
        self.assertEqual(response.status_code, 302)
        # 验证会话中用户已认证
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_profile_requires_login(self):
        """测试未登录用户访问个人中心被拦截"""
        response = self.client.get(self.profile_url)
        # 未登录应重定向到登录页
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(self.login_url))