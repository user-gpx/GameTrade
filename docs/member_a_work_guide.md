# 成员 A 工作指南

## 目标概述
负责 **用户认证模块** 和 **道具展示模块** 的完整开发，包括模型设计、视图逻辑、模板页面、URL 配置、数据库迁移、单元测试，并与其他成员协调确保风格与数据一致。

---

## 第一阶段：环境准备与项目配置

### 1.1 确认开发环境
**为什么需要这一步？**
- 确保 Python、Django 以及依赖库版本正确，避免导入错误或兼容性问题。
- 虚拟环境隔离项目依赖，防止与其他项目冲突。
- 启动开发服务器验证基础配置（settings、数据库）是否正确。

```bash
# 激活虚拟环境
conda activate gametrade

# 安装依赖
pip install -r requirements.txt

# 测试 Django 是否正常
python manage.py runserver
```
访问 `http://127.0.0.1:8000/admin/` 确认项目可运行。

### 1.2 配置媒体文件支持（头像/道具图片上传）
**为什么需要这一步？**
- Django 默认只处理静态资源，不处理用户上传文件。
- `MEDIA_ROOT` 指定上传文件存储位置，`MEDIA_URL` 指定访问 URL 前缀。
- 开发环境需手动配置 `static()` 提供媒体访问，否则头像/图片无法显示。

**操作内容**
- 修改现有文件  
  1. `config/settings.py`：添加媒体相关配置。
     ```python
     # Media files (用户上传文件)
     MEDIA_URL = '/media/'
     MEDIA_ROOT = BASE_DIR / 'media'
     ```
  2. `config/urls.py`：在开发环境下通过 `static()` 暴露上传文件。
     ```python
     from django.conf import settings
     from django.conf.urls.static import static

     urlpatterns = [
         path('admin/', admin.site.urls),
         # 后续添加 users 和 items 的路由
     ]

     if settings.DEBUG:
         urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
     ```

---

## 第二阶段：用户认证模块开发

### 2.1 创建用户模型
**为什么需要这一步？**
- 默认 User 模型字段不足（缺少手机号、余额、头像）。
- 继承 `AbstractUser` 保留 Django 认证功能并扩展字段。
- 早期确定自定义模型避免后续迁移困难。
- `upload_to` 指定头像存储子目录，`db_table` 与文档一致，方便协作。

**修改现有文件**
- `apps/users/models.py`：
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField('手机号', max_length=11, blank=True)
    balance = models.DecimalField('余额', max_digits=10, decimal_places=2, default=0)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)

    class Meta:
        db_table = 'users_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
```

### 2.2 注册自定义用户模型
**为什么需要这一步？**
- `INSTALLED_APPS` 告诉 Django 需要加载哪些应用。
- `AUTH_USER_MODEL` 必须在首次迁移前指定，否则会创建默认表导致冲突。
- 其他模块（如道具模型）通过 `settings.AUTH_USER_MODEL` 引用正确的用户模型。

**操作内容**
- 修改现有文件  
  1. `config/settings.py`：登记应用并指定自定义用户模型。
     ```python
     INSTALLED_APPS = [
         'django.contrib.admin',
         'django.contrib.auth',
         'django.contrib.contenttypes',
         'django.contrib.sessions',
         'django.contrib.messages',
         'django.contrib.staticfiles',
         'apps.users',
         'apps.items',
     ]

     AUTH_USER_MODEL = 'users.User'
     ```

### 2.3 创建用户表单
**为什么需要这一步？**
- Django 表单负责验证输入（邮箱格式、密码强度），防止无效/危险数据。
- `UserCreationForm` 自动处理密码加密和确认逻辑。
- 在 `__init__` 中添加 `form-control` 类以匹配 Bootstrap 风格。
- `ProfileForm` 使用 `ModelForm` 自动生成字段，减少重复代码。

**需新建文件：`apps/users/forms.py`**
```python
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='邮箱')
    phone = forms.CharField(max_length=11, required=False, label='手机号')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'avatar')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
```

### 2.4 创建用户视图
**为什么需要这一步？**
- 视图处理请求并返回响应，是业务逻辑的核心。
- `register_view` 保存用户后自动登录，提升体验。
- `login_view` 使用 `authenticate`/`login` 确保安全。
- `@login_required` 保护需要登录的页面。
- `messages` 框架用于反馈操作结果。
- 头像上传需要 `request.FILES` 并在模板中设置 `enctype`。

**修改现有文件：`apps/users/views.py`**
```python
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('items:list')
        messages.error(request, '注册失败，请检查输入信息。')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{user.username}！')
                return redirect('items:list')
        messages.error(request, '用户名或密码错误。')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, '您已成功退出。')
    return redirect('users:login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})
```

### 2.5 配置用户 URL
**为什么需要这一步？**
- URL 将路径映射到视图，是 Web 应用入口。
- `app_name` 提供命名空间，避免冲突，并可在模板中使用 `{% url 'users:login' %}`。
- 组长要求“所有 URL 必须在各自 app 的 `urls.py` 中集中维护，主路由只负责 `include`”，这样便于模块解耦、统一管理。
- 主 `config/urls.py` 中只写一条 `path('users/', include(...))`，而不是逐条添加。

**操作内容**
- 新建文件  
  1. `apps/users/urls.py`：集中管理用户模块路由。
     ```python
     from django.urls import path
     from . import views

     app_name = 'users'

     urlpatterns = [
         path('register/', views.register_view, name='register'),
         path('login/', views.login_view, name='login'),
         path('logout/', views.logout_view, name='logout'),
         path('profile/', views.profile_view, name='profile'),
     ]
     ```
- 修改现有文件  
  1. `config/urls.py`：仅通过一条 `path('users/', include(...))` 引入用户模块。
     ```python
     from django.urls import path, include

     urlpatterns = [
         path('admin/', admin.site.urls),
         path('users/', include('apps.users.urls')),
         # path('items/', include('apps.items.urls')) 后续添加
     ]
     ```

### 2.6 创建用户模板
**为什么需要这一步？**
- 模板负责展示层，继承 `base.html` 获得统一布局。
- `{% csrf_token %}` 防止 CSRF 攻击。
- `{{ form.as_p }}` 自动渲染字段与错误信息。
- `{% url %}` 动态生成链接，避免硬编码。
- 头像上传需要 `enctype="multipart/form-data"`。

**操作内容**
- 新建模板文件（路径相对于 `templates/` 目录）：
  1. `users/register.html`
  2. `users/login.html`
  3. `users/profile.html`
- 下面示例展示 `users/profile.html` 的结构：
```html
{% extends 'base.html' %}
{% block title %}个人资料{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-8">
    <div class="card">
      <div class="card-header"><h4><i class="fas fa-user-circle"></i> 个人资料</h4></div>
      <div class="card-body">
        <div class="row mb-3">
          <div class="col-md-3 text-center">
            {% if user.avatar %}
              <img src="{{ user.avatar.url }}" class="img-thumbnail" alt="头像" style="max-width:150px;">
            {% else %}
              <i class="fas fa-user-circle fa-5x text-secondary"></i>
            {% endif %}
          </div>
          <div class="col-md-9">
            <p><strong>用户名：</strong>{{ user.username }}</p>
            <p><strong>余额：</strong>¥{{ user.balance }}</p>
            <p><strong>注册时间：</strong>{{ user.date_joined|date:"Y-m-d H:i" }}</p>
          </div>
        </div>
        <hr>
        <form method="post" enctype="multipart/form-data">
          {% csrf_token %}
          {{ form.as_p }}
          <button type="submit" class="btn btn-primary">保存修改</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### 2.7 执行数据库迁移
**为什么需要这一步？**
- ORM 模型需通过迁移同步到数据库。
- `makemigrations` 生成迁移脚本，`migrate` 执行脚本创建表。
- 迁移文件应纳入版本控制，确保团队数据库一致。
- `createsuperuser` 创建后台账号方便测试。

**操作内容（命令行）**
```bash
python manage.py makemigrations users   # 检测模型变更，生成迁移脚本
python manage.py migrate               # 执行迁移，创建/更新数据表
python manage.py createsuperuser       # 创建超级用户，用于后台管理
```

### 2.8 编写用户模块测试
**为什么需要这一步？**
- 自动化测试防止回归，作为“活文档”说明功能预期。
- `TestCase` 使用独立测试数据库，互不干扰。
- 覆盖注册、登录、权限等核心流程。

**操作内容**
- 修改现有文件：`apps/users/tests.py`
```python
from django.test import TestCase, Client
from django.urls import reverse
from .models import User

class UserAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')

    def test_user_registration(self):
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_login(self):
        User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_profile_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
```

运行测试：
```bash
python manage.py test apps.users
```

---

## 第三阶段：道具展示模块开发

### 3.1 与成员 B 协调道具模型字段
**为什么需要这一步？**
- 成员 B 的交易功能依赖同一份道具数据，必须统一字段定义。
- 字段类型（例如价格用 `DecimalField`）影响精度与查询。
- 外键/状态定义须一致，避免后期迁移反复修改。

**关键点**：确认价格字段、卖家外键、状态枚举及额外需求。

### 3.2 创建道具模型
**为什么需要这一步？**
- 道具模型是业务核心，存储商品信息并建立与用户的关系。
- 使用 `choices` 控制分类/状态值，防止脏数据。
- `related_name` 便于反向查询，`ordering` 默认按发布时间排序。
- 收藏模型 `Favorite` 通过 `unique_together` 防止重复收藏。

**文件：`apps/items/models.py`**
```python
from django.db import models
from django.conf import settings

class GameItem(models.Model):
    STATUS_CHOICES = [
        ('available', '在售'),
        ('sold', '已售'),
        ('offline', '下架'),
    ]
    CATEGORY_CHOICES = [
        ('weapon', '武器'),
        ('armor', '防具'),
        ('consumable', '消耗品'),
        ('material', '材料'),
        ('other', '其他'),
    ]

    name = models.CharField('道具名称', max_length=100)
    category = models.CharField('分类', max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='卖家', related_name='items')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField('图片', upload_to='items/', blank=True, null=True)
    description = models.TextField('描述', blank=True)
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'items_gameitem'
        ordering = ['-created_at']
        verbose_name = '游戏道具'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name='用户', related_name='favorites')
    item = models.ForeignKey(GameItem, on_delete=models.CASCADE,
                             verbose_name='道具', related_name='favorited_by')
    created_at = models.DateTimeField('收藏时间', auto_now_add=True)

    class Meta:
        db_table = 'items_favorite'
        unique_together = ('user', 'item')
        verbose_name = '收藏'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.user.username} - {self.item.name}'
```

### 3.3 注册道具应用
**为什么需要这一步？**
- 未在 `INSTALLED_APPS` 注册则不会检测模型、生成迁移。
- 确认 `apps.items` 已加入配置。

### 3.4 创建道具视图
**为什么需要这一步？**
- `item_list` 实现搜索、筛选、排序、分页，满足浏览需求。
- `Q` 对象支持模糊查询，`Paginator` 控制数据量。
- `item_detail` 根据登录状态展示收藏按钮。
- `toggle_favorite` 使用 `get_or_create` 简化收藏切换，`@login_required` 保护权限。
- `favorite_list` 使用 `select_related` 减少查询次数。

**文件：`apps/items/views.py`**
```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import GameItem, Favorite

def item_list(request):
    items = GameItem.objects.filter(status='available')
    search = request.GET.get('search', '')
    if search:
        items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))
    category = request.GET.get('category', '')
    if category:
        items = items.filter(category=category)
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price', '-price', 'created_at', '-created_at']:
        items = items.order_by(sort)
    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'items/list.html', {
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'sort': sort,
        'categories': GameItem.CATEGORY_CHOICES,
    })

def item_detail(request, pk):
    item = get_object_or_404(GameItem, pk=pk)
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, item=item).exists()
    return render(request, 'items/detail.html', {'item': item, 'is_favorited': is_favorited})

@login_required
def toggle_favorite(request, pk):
    item = get_object_or_404(GameItem, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, item=item)
    if not created:
        favorite.delete()
        messages.info(request, '已取消收藏。')
    else:
        messages.success(request, '收藏成功！')
    return redirect('items:detail', pk=pk)

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('item')
    return render(request, 'items/favorites.html', {'favorites': favorites})
```

### 3.5 配置道具 URL
**为什么需要这一步？**
- URL 路由映射请求路径到视图。
- `<int:pk>` 捕获道具 ID，命名空间防止冲突。
- 同样遵守组长规范：只在 `apps/items/urls.py` 中新增具体路由，再在 `config/urls.py` 中使用单条 `include` 引入 `items` 模块。

**文件：`apps/items/urls.py`**
```python
from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    path('', views.item_list, name='list'),
    path('<int:pk>/', views.item_detail, name='detail'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorite_list, name='favorites'),
]
```

**文件：`config/urls.py`**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
    path('items/', include('apps.items.urls')),
]
```

### 3.6 创建道具模板
**为什么需要这一步？**
- 模板呈现数据，使用 Bootstrap 网格打造卡片式列表。
- 搜索表单使用 GET 以保留参数。
- 分页链接附带现有查询参数，避免条件丢失。
- `{% empty %}` 处理无数据情况，提升体验。
- 详情页根据 `is_favorited` 切换按钮样式。

**目录结构**
```
templates/
  items/
    list.html
    detail.html
    favorites.html
```

### 3.7 执行道具模块迁移
**为什么需要这一步？**
- 将 GameItem/Favorite 模型同步到数据库。
- 迁移文件记录结构变化，便于版本追踪。

```bash
python manage.py makemigrations items
python manage.py migrate
```

### 3.8 编写道具模块测试
**为什么需要这一步？**
- 验证列表、详情、搜索、收藏等功能。
- 测试权限，确保收藏列表需要登录。
- 自动化测试便于后续迭代。

**文件：`apps/items/tests.py`**
```python
from django.test import TestCase, Client
from django.urls import reverse
from apps.users.models import User
from .models import GameItem, Favorite

class ItemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='TestPass123!')
        self.seller = User.objects.create_user(username='seller', password='TestPass123!')
        self.item = GameItem.objects.create(
            name='测试道具',
            category='weapon',
            price=100,
            seller=self.seller,
            description='测试描述'
        )

    def test_item_list(self):
        response = self.client.get(reverse('items:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '测试道具')

    def test_item_detail(self):
        response = self.client.get(reverse('items:detail', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100')

    def test_search(self):
        response = self.client.get(reverse('items:list') + '?search=测试')
        self.assertContains(response, '测试道具')

    def test_toggle_favorite(self):
        self.client.login(username='buyer', password='TestPass123!')
        url = reverse('items:toggle_favorite', args=[self.item.pk])
        self.client.get(url)
        self.assertTrue(Favorite.objects.filter(user=self.user, item=self.item).exists())
        self.client.get(url)
        self.assertFalse(Favorite.objects.filter(user=self.user, item=self.item).exists())

    def test_favorites_requires_login(self):
        response = self.client.get(reverse('items:favorites'))
        self.assertEqual(response.status_code, 302)
```

```bash
python manage.py test apps.items
```

---

## 第四阶段：整合与优化

### 4.1 更新导航链接
**为什么需要这一步？**
- 导航是用户进入各模块的入口，必须确保链接正确。
- 使用 `{% url %}` 替代硬编码，当路由调整时无需修改模板。

**文件：`templates/includes/header.html`**
- `{% url 'items:list' %}`
- `{% url 'users:login' %}` / `{% url 'users:register' %}` / `{% url 'users:profile' %}` / `{% url 'users:logout' %}`

### 4.2 配置登录相关重定向
**为什么需要这一步？**
- `LOGIN_URL` 与 `@login_required` 配合，指定未登录访问的跳转路径。
- `LOGIN_REDIRECT_URL` 决定登录成功后进入的页面。
- `LOGOUT_REDIRECT_URL` 指定登出后跳转位置。

```python
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/items/'
LOGOUT_REDIRECT_URL = '/users/login/'
```

### 4.3 创建首页（可选）
**为什么需要这一步？**
- 首页展示最新道具，提供统一入口。
- 可复用道具查询逻辑，展示最近 8 个在售道具。

```python
# apps/items/views.py
def home(request):
    latest = GameItem.objects.filter(status='available')[:8]
    return render(request, 'pages/home.html', {'latest_items': latest})

# config/urls.py
from apps.items import views as item_views
urlpatterns = [
    path('', item_views.home, name='home'),
    ...
]
```

### 4.4 在 Admin 中注册模型
**为什么需要这一步？**
- Admin 提供数据管理界面，方便调试/录入测试数据。
- 自定义列表显示、筛选条件提升效率。

```python
# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone', 'balance', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('额外信息', {'fields': ('phone', 'balance', 'avatar')}),
    )

# apps/items/admin.py
from django.contrib import admin
from .models import GameItem, Favorite

@admin.register(GameItem)
class GameItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'seller', 'status', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'created_at']
```

---

## 第五阶段：测试与验证

### 5.1 运行完整测试套件
**为什么需要这一步？**
- 提交前跑测试确保新功能未破坏旧功能。
- `python manage.py test` 自动发现所有测试，提供报告。
- 分模块运行便于定位问题。

```bash
python manage.py test
python manage.py test apps.users
python manage.py test apps.items
```

### 5.2 手动功能测试清单
**为什么需要这一步？**
- 自动化测试无法覆盖视觉/交互问题，需要人工验证。
- 清单保证不遗漏关键流程，真实浏览器可发现兼容性问题。

- [ ] 注册成功并自动登录
- [ ] 登录/登出流程正确
- [ ] 个人资料页显示与头像上传正常
- [ ] 道具列表分页/筛选/排序工作正常
- [ ] 搜索结果正确
- [ ] 详情页信息完整
- [ ] 收藏/取消收藏功能正常
- [ ] 收藏列表显示正确
- [ ] 未登录访问受保护页面自动跳转登录页

### 5.3 创建测试数据（可选）
**为什么需要这一步？**
- 批量生成演示数据便于测试分页/搜索。
- 管理命令可重复使用，快速准备环境。

```python
# apps/items/management/commands/create_test_data.py
from django.core管理 base import BaseCommand
from apps.users.models import User
from apps.items.models import GameItem

class Command(BaseCommand):
    help = '创建测试数据'

    def handle(self, *args, **options):
        seller = User.objects.create_user('seller1', 'seller@example.com', 'TestPass123!')
        categories = ['weapon', 'armor', 'consumable
