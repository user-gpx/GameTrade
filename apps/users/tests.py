"""
Users 模块测试套件

测试方法论:
- 白盒测试: 语句覆盖、条件覆盖、基本路径覆盖
- 黑盒测试: 等价类划分、边界值分析、判定表、场景法
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import RegisterForm, UserForm, ProfileForm


# ============================================================
#  白盒测试 — 语句覆盖、条件覆盖、基本路径覆盖
# ============================================================

class UserAuthWhiteBoxTests(TestCase):
    """用户认证模块白盒测试 — 覆盖每个分支/路径"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        self.profile_url = reverse('users:profile')
        self.edit_profile_url = reverse('users:edit_profile')

    # ---------- register 视图 ----------

    def test_register_get_renders_form(self):
        """语句覆盖: GET 请求返回注册页面"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_post_valid_creates_user(self):
        """语句覆盖: POST 有效数据 → 创建用户 → 自动登录 → 重定向"""
        response = self.client.post(self.register_url, {
            'username': 'newuser', 'email': 'new@test.com',
            'password1': 'ComplexPass1!', 'password2': 'ComplexPass1!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_post_invalid_password_mismatch(self):
        """条件覆盖: 密码不匹配 → 留在注册页"""
        response = self.client.post(self.register_url, {
            'username': 'baduser', 'email': 'bad@test.com',
            'password1': 'ComplexPass1!', 'password2': 'WrongPass1!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_register_authenticated_redirect(self):
        """条件覆盖: 已登录用户访问注册页 → 重定向到首页"""
        User.objects.create_user(username='logged', password='TestPass1!')
        self.client.login(username='logged', password='TestPass1!')
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    # ---------- login 视图 ----------

    def test_login_get_renders_form(self):
        """语句覆盖: GET 请求返回登录页面"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login_post_valid_credentials(self):
        """语句覆盖: POST 有效凭证 → 登录 → 重定向"""
        User.objects.create_user(username='loginuser', password='TestPass1!')
        response = self.client.post(self.login_url, {
            'username': 'loginuser', 'password': 'TestPass1!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_post_invalid_wrong_password(self):
        """条件覆盖: 密码错误 → 返回401/200 并显示错误"""
        User.objects.create_user(username='wrongpw', password='TestPass1!')
        response = self.client.post(self.login_url, {
            'username': 'wrongpw', 'password': 'BadPass1!',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_post_invalid_nonexistent_user(self):
        """条件覆盖: 不存在的用户 → 返回错误"""
        response = self.client.post(self.login_url, {
            'username': 'noone', 'password': 'NoPass1!',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_with_next_parameter(self):
        """条件覆盖: 登录后跳转 next 参数指定的路径"""
        User.objects.create_user(username='nextuser', password='TestPass1!')
        response = self.client.post(
            self.login_url + '?next=/items/',
            {'username': 'nextuser', 'password': 'TestPass1!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/items/')

    def test_login_already_authenticated_redirect(self):
        """条件覆盖: 已登录用户访问登录页 → 重定向"""
        User.objects.create_user(username='already', password='TestPass1!')
        self.client.login(username='already', password='TestPass1!')
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)

    # ---------- logout 视图 ----------

    def test_logout_clears_session_and_redirects(self):
        """语句覆盖: 登出 → 清除会话 → 重定向"""
        User.objects.create_user(username='logoutuser', password='TestPass1!')
        self.client.login(username='logoutuser', password='TestPass1!')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    # ---------- profile 视图 ----------

    def test_profile_requires_login(self):
        """条件覆盖: 未登录 → 302 重定向到登录页"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_render_for_logged_in(self):
        """语句覆盖: 已登录 → 200 并渲染用户资料"""
        user = User.objects.create_user(username='profileuser', password='TestPass1!')
        self.client.login(username='profileuser', password='TestPass1!')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'profileuser')

    def test_profile_includes_user_items(self):
        """语句覆盖: 用户资料页包含发布的道具"""
        from items.models import Item
        user = User.objects.create_user(username='sellerprof', password='TestPass1!')
        self.client.login(username='sellerprof', password='TestPass1!')
        Item.objects.create(
            name='TestItem', price=1.00, seller=user,
            status='available', game='other',
        )
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'TestItem')

    # ---------- edit_profile 视图 ----------

    def test_edit_profile_get_renders_form(self):
        """语句覆盖: GET → 渲染编辑表单"""
        user = User.objects.create_user(username='edituser', password='TestPass1!')
        self.client.login(username='edituser', password='TestPass1!')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')

    def test_edit_profile_post_valid_updates_both_forms(self):
        """语句覆盖: POST 有效 → 更新 User + Profile → 重定向"""
        user = User.objects.create_user(username='edit2', password='TestPass1!')
        self.client.login(username='edit2', password='TestPass1!')
        response = self.client.post(self.edit_profile_url, {
            'username': 'edit2', 'email': 'newemail@test.com',
            'phone': '13800138000', 'bio': 'Hello world',
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, 'newemail@test.com')
        self.assertEqual(user.profile.phone, '13800138000')

    def test_edit_profile_post_invalid_returns_form(self):
        """条件覆盖: POST 无效 → 返回表单带错误"""
        user = User.objects.create_user(username='edit3', password='TestPass1!')
        self.client.login(username='edit3', password='TestPass1!')
        response = self.client.post(self.edit_profile_url, {
            'username': '',
            'email': 'invalid-email',
        })
        self.assertEqual(response.status_code, 200)


class UserFormWhiteBoxTests(TestCase):
    """表单白盒测试 — 覆盖每个验证分支"""

    def test_register_form_valid(self):
        """语句覆盖: 所有字段有效"""
        data = {'username': 'formuser', 'email': 'form@test.com',
                'password1': 'ComplexPass1!', 'password2': 'ComplexPass1!'}
        form = RegisterForm(data)
        self.assertTrue(form.is_valid())

    def test_register_form_missing_email(self):
        """条件覆盖: email 必填"""
        data = {'username': 'nouser', 'password1': 'Complex1!', 'password2': 'Complex1!'}
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_register_form_password_too_short(self):
        """条件覆盖: 密码太短"""
        data = {'username': 'shortpw', 'email': 's@t.com',
                'password1': 'Ab1!', 'password2': 'Ab1!'}
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())

    def test_register_form_duplicate_email(self):
        """条件覆盖: clean_email — 邮箱已被注册"""
        User.objects.create_user(username='existing', email='dup@test.com',
                                 password='TestPass1!')
        data = {'username': 'newbie', 'email': 'dup@test.com',
                'password1': 'Complex1!', 'password2': 'Complex1!'}
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_register_form_duplicate_username(self):
        """条件覆盖: 用户名已存在"""
        User.objects.create_user(username='dupuser', email='a@t.com',
                                 password='TestPass1!')
        data = {'username': 'dupuser', 'email': 'b@t.com',
                'password1': 'Complex1!', 'password2': 'Complex1!'}
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_user_form_valid(self):
        """语句覆盖: UserForm 有效更新"""
        user = User.objects.create_user(username='uf', password='TestPass1!')
        form = UserForm({'username': 'uf', 'email': 'u@t.com'}, instance=user)
        self.assertTrue(form.is_valid())

    def test_profile_form_valid(self):
        """语句覆盖: ProfileForm 有效数据"""
        user = User.objects.create_user(username='pf', password='TestPass1!')
        form = ProfileForm({'phone': '13900139000', 'bio': 'Hi'}, instance=user.profile)
        self.assertTrue(form.is_valid())

    def test_profile_form_phone_too_long(self):
        """条件覆盖: phone 超长"""
        user = User.objects.create_user(username='longphone', password='TestPass1!')
        form = ProfileForm({'phone': '1' * 21, 'bio': 'ok'}, instance=user.profile)
        self.assertFalse(form.is_valid())

    def test_profile_form_bio_too_long(self):
        """条件覆盖: bio 超过 500 字符"""
        user = User.objects.create_user(username='longbio', password='TestPass1!')
        form = ProfileForm({'phone': '', 'bio': 'x' * 501}, instance=user.profile)
        self.assertFalse(form.is_valid())


class UserModelWhiteBoxTests(TestCase):
    """模型白盒测试 — 覆盖每个方法"""

    def test_userprofile_signal_auto_create(self):
        """语句覆盖: 创建 User 时自动创建 UserProfile"""
        user = User.objects.create_user(username='signal', password='TestPass1!')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)

    def test_userprofile_signal_auto_save(self):
        """语句覆盖: 保存 User 时自动保存 profile"""
        user = User.objects.create_user(username='autosave', password='TestPass1!')
        user.email = 'new@test.com'
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.email, 'new@test.com')

    def test_get_avatar_url_with_avatar(self):
        """条件覆盖: 有头像 → 返回 avatar.url"""
        user = User.objects.create_user(username='avat', password='TestPass1!')
        # 无头像时走 else 分支
        url = user.profile.get_avatar_url()
        self.assertEqual(url, '/static/images/default_avatar.png')

    def test_get_avatar_url_default(self):
        """条件覆盖: 无头像 → 返回默认头像路径"""
        user = User.objects.create_user(username='noav', password='TestPass1!')
        result = user.profile.get_avatar_url()
        self.assertTrue(result.endswith('default_avatar.png'))

    def test_userprofile_str(self):
        """语句覆盖: __str__"""
        user = User.objects.create_user(username='strtest', password='TestPass1!')
        self.assertIn('strtest', str(user.profile))


# ============================================================
#  黑盒测试 — 等价类划分、边界值分析、判定表、场景法、因果图
# ============================================================

class UserBlackBoxEquivalenceClass(TestCase):
    """等价类划分测试 — 将输入数据划分为有效等价类和无效等价类"""

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('users:register')
        cls.login_url = reverse('users:login')

    # ---- 注册 — 等价类 ----

    def test_username_valid_normal(self):
        """有效等价类: 正常长度、字母数字混合"""
        r = self.client.post(self.register_url, {
            'username': 'Player001', 'email': 'p1@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_username_valid_chinese(self):
        """有效等价类: 含中文用户名"""
        r = self.client.post(self.register_url, {
            'username': '玩家张三', 'email': 'zhang@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_username_invalid_empty(self):
        """无效等价类: 空用户名"""
        r = self.client.post(self.register_url, {
            'username': '', 'email': 'empty@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 200)

    def test_email_invalid_format(self):
        """无效等价类: 错误邮箱格式"""
        r = self.client.post(self.register_url, {
            'username': 'badmail', 'email': 'notanemail',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 200)

    def test_email_empty(self):
        """无效等价类: 空邮箱"""
        r = self.client.post(self.register_url, {
            'username': 'noemail', 'email': '',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 200)

    def test_password_valid_complex(self):
        """有效等价类: 复杂密码"""
        r = self.client.post(self.register_url, {
            'username': 'complexpw', 'email': 'c@t.com',
            'password1': 'Abc@1234#', 'password2': 'Abc@1234#',
        })
        self.assertEqual(r.status_code, 302)

    def test_password_invalid_numeric_only(self):
        """无效等价类: 纯数字密码（Django 默认密码验证器）"""
        r = self.client.post(self.register_url, {
            'username': 'numpw', 'email': 'n@t.com',
            'password1': '12345678', 'password2': '12345678',
        })
        self.assertEqual(r.status_code, 200)

    # ---- 登录 — 等价类 ----

    def test_login_valid_username(self):
        """有效等价类: 用户名登录"""
        User.objects.create_user(username='login001', password='TestPass1!')
        r = self.client.post(self.login_url, {
            'username': 'login001', 'password': 'TestPass1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_login_invalid_empty_username(self):
        """无效等价类: 空用户名"""
        r = self.client.post(self.login_url, {
            'username': '', 'password': 'TestPass1!',
        })
        self.assertEqual(r.status_code, 200)

    def test_login_invalid_empty_password(self):
        """无效等价类: 空密码"""
        r = self.client.post(self.login_url, {
            'username': 'someone', 'password': '',
        })
        self.assertEqual(r.status_code, 200)


class UserBlackBoxBoundaryValue(TestCase):
    """边界值分析测试 — 测试输入域的边界"""

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse('users:register')
        cls.edit_profile_url = reverse('users:edit_profile')

    # ---- 用户名边界 ----

    def test_username_boundary_min_1_char(self):
        """边界值: 用户名 1 个字符"""
        r = self.client.post(self.register_url, {
            'username': 'a', 'email': 'min@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_username_boundary_max_150_chars(self):
        """边界值: 用户名 150 个字符"""
        long_name = 'u' * 150
        r = self.client.post(self.register_url, {
            'username': long_name, 'email': 'long@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_username_exceed_max(self):
        """边界值: 用户名 >150 字符"""
        too_long = 'u' * 151
        r = self.client.post(self.register_url, {
            'username': too_long, 'email': 'toomuch@t.com',
            'password1': 'ValidPass1!', 'password2': 'ValidPass1!',
        })
        self.assertEqual(r.status_code, 200)

    # ---- 密码边界 ----

    def test_password_boundary_min_8_chars(self):
        """边界值: 密码恰好 8 位"""
        r = self.client.post(self.register_url, {
            'username': 'pw8', 'email': 'p8@t.com',
            'password1': 'Abcd1@34', 'password2': 'Abcd1@34',
        })
        self.assertEqual(r.status_code, 302)

    # ---- 个人简介边界 ----

    def test_bio_boundary_max_500_chars(self):
        """边界值: 简介恰好 500 字符"""
        user = User.objects.create_user(username='bio500', password='TestPass1!')
        self.client.login(username='bio500', password='TestPass1!')
        r = self.client.post(self.edit_profile_url, {
            'username': 'bio500', 'email': 'b@t.com',
            'bio': 'x' * 500, 'phone': '',
        })
        self.assertEqual(r.status_code, 302)

    def test_bio_boundary_501_chars_exceeds(self):
        """边界值: 简介 501 字符超限"""
        user = User.objects.create_user(username='bio501', password='TestPass1!')
        self.client.login(username='bio501', password='TestPass1!')
        r = self.client.post(self.edit_profile_url, {
            'username': 'bio501', 'email': 'b1@t.com',
            'bio': 'x' * 501, 'phone': '',
        })
        self.assertEqual(r.status_code, 200)

    # ---- 手机号边界 ----

    def test_phone_boundary_max_20_chars(self):
        """边界值: 手机号恰好 20 字符"""
        user = User.objects.create_user(username='ph20', password='TestPass1!')
        self.client.login(username='ph20', password='TestPass1!')
        r = self.client.post(self.edit_profile_url, {
            'username': 'ph20', 'email': 'p20@t.com',
            'phone': '1' * 20, 'bio': '',
        })
        self.assertEqual(r.status_code, 302)


class UserBlackBoxDecisionTable(TestCase):
    """判定表测试 — 多条件组合"""

    @classmethod
    def setUpTestData(cls):
        cls.login_url = reverse('users:login')
        cls.register_url = reverse('users:register')

    def setUp(self):
        self.user = User.objects.create_user(
            username='dtuser', email='dt@test.com', password='Correct1!',
        )

    def test_correct_user_correct_pw(self):
        """判定: 正确用户名 + 正确密码 → 登录成功"""
        r = self.client.post(self.login_url, {
            'username': 'dtuser', 'password': 'Correct1!',
        })
        self.assertEqual(r.status_code, 302)

    def test_correct_user_wrong_pw(self):
        """判定: 正确用户名 + 错误密码 → 登录失败"""
        r = self.client.post(self.login_url, {
            'username': 'dtuser', 'password': 'Wrong1!!',
        })
        self.assertEqual(r.status_code, 200)

    def test_wrong_user_any_pw(self):
        """判定: 不存在用户名 + 任意密码 → 登录失败"""
        r = self.client.post(self.login_url, {
            'username': 'ghost', 'password': 'Correct1!',
        })
        self.assertEqual(r.status_code, 200)

    def test_empty_all_fields(self):
        """判定: 空用户名 + 空密码 → 登录失败"""
        r = self.client.post(self.login_url, {
            'username': '', 'password': '',
        })
        self.assertEqual(r.status_code, 200)

    def test_register_decision_passwords_match_strong(self):
        """判定: 密码匹配 + 强度够 → 注册成功"""
        r = self.client.post(self.register_url, {
            'username': 'decision1', 'email': 'd1@t.com',
            'password1': 'Strong1!@', 'password2': 'Strong1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_register_decision_passwords_match_weak(self):
        """判定: 密码匹配 + 弱密码 → 注册失败"""
        r = self.client.post(self.register_url, {
            'username': 'decision2', 'email': 'd2@t.com',
            'password1': '12345678', 'password2': '12345678',
        })
        self.assertEqual(r.status_code, 200)

    def test_register_decision_passwords_mismatch(self):
        """判定: 密码不匹配 → 注册失败"""
        r = self.client.post(self.register_url, {
            'username': 'decision3', 'email': 'd3@t.com',
            'password1': 'Strong1!@', 'password2': 'Different1!@',
        })
        self.assertEqual(r.status_code, 200)

    def test_register_decision_email_exists(self):
        """判定: 邮箱已存在 → 注册失败"""
        r = self.client.post(self.register_url, {
            'username': 'decision4', 'email': 'dt@test.com',  # same as setup
            'password1': 'Strong1!@', 'password2': 'Strong1!@',
        })
        self.assertEqual(r.status_code, 200)


class UserBlackBoxScenarioTests(TestCase):
    """场景法测试 — 完整用户旅程"""

    def setUp(self):
        self.client = Client()

    def test_full_user_journey(self):
        """场景: 注册 → 查看个人资料 → 编辑资料 → 登出 → 登录"""
        # Step 1: 注册
        r = self.client.post(reverse('users:register'), {
            'username': 'journey', 'email': 'journey@test.com',
            'password1': 'Complex1!@', 'password2': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

        # 注册后已在登录状态，直接查看资料
        self.assertTrue(User.objects.filter(username='journey').exists())

        # Step 2: 查看个人资料
        r = self.client.get(reverse('users:profile'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'journey')

        # Step 3: 编辑资料
        r = self.client.post(reverse('users:edit_profile'), {
            'username': 'journey', 'email': 'journey_new@test.com',
            'phone': '18888888888', 'bio': '游戏达人',
        })
        self.assertEqual(r.status_code, 302)

        # 验证编辑生效
        r = self.client.get(reverse('users:profile'))
        self.assertContains(r, 'journey_new@test.com')

        # Step 4: 登出
        r = self.client.get(reverse('users:logout'))
        self.assertEqual(r.status_code, 302)

        # Step 5: 重新登录
        r = self.client.post(reverse('users:login'), {
            'username': 'journey', 'password': 'Complex1!@',
        })
        self.assertEqual(r.status_code, 302)

    def test_guest_cannot_access_protected_pages(self):
        """场景: 未登录游客无法访问受保护的页面"""
        protected_urls = [
            reverse('users:profile'),
            reverse('users:edit_profile'),
        ]
        for url in protected_urls:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302,
                             f'URL {url} 应该拦截未登录用户')
