# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在本仓库中工作时提供指引。

## 环境与命令

```bash
# 创建并激活 conda 环境

conda activate gametrade

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python manage.py runserver

# 运行全部测试
python manage.py test

# 运行单个 app 的测试
python manage.py test apps.users.tests
python manage.py test apps.items.tests

# 运行指定的测试用例或方法
python manage.py test apps.users.tests.UserAuthTestCase
python manage.py test apps.users.tests.UserAuthTestCase.test_user_registration

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# Django shell
python manage.py shell
```

## 项目架构

这是一个基于 Django 4.2 的游戏道具交易平台。Django 项目根目录为 `config/`（settings、urls、wsgi）。所有 app 均位于 `apps/` 目录下，该目录已被注入 `sys.path`，因此 app 可直接按名称导入（例如 `import items`，而非 `import apps.items`）。

### 各 App 及实现状态

| App | 状态 | 功能 |
|-----|------|------|
| `users` | 已完成 | 认证（注册/登录/登出）、UserProfile（与 User 一对一扩展）、个人资料编辑 |
| `items` | 已完成 | 道具增删改查、分类、收藏、搜索/筛选/分页 |
| `orders` | 仅骨架 | 交易订单 — 空模型，无视图 |
| `payments` | 仅骨架 | 支付处理 — 空模型，无视图 |
| `trading` | 仅骨架 | 交易执行 — 空模型，无视图 |
| `stats` | 原型阶段 | 包含带路径参数和查询字符串的原型视图，无模型 |

### 核心模型

- **UserProfile**（`users.models`）：Django `User` 的一对一扩展。字段：avatar（ImageField）、phone、bio、balance（DecimalField）。通过 `post_save` 信号在创建 User 时自动创建并自动保存 —— 在代码中创建用户后，无需手动对 profile 调用 `.save()`，`.profile` 始终可用。
- **Category**（`items.models`）：道具分类，包含 `icon`（Font Awesome 的 CSS 类字符串），name 唯一。
- **Item**（`items.models`）：核心实体。字段：name、category（外键，SET_NULL）、game（可选值：lol/csgo/dota2/genshin/pubg/valorant/wow/other）、price、description、image、seller（外键→User）、status（available/sold/off_shelf）、views_count。默认排序：`-created_at`。
- **Favorite**（`items.models`）：User→Item 多对多关系，`unique_together('user', 'item')`。

### URL 结构

- `/` — 首页（TemplateView）
- `/users/` — 认证相关 URL（register、login、logout、profile、edit_profile）
- `/items/` — 道具列表、发布、详情、编辑、删除、收藏、我的发布
- `/stats/` — 原型仪表盘端点
- `/admin/` — Django 管理后台

### 前端

模板使用 Django 模板继承，基模板为 `base.html`（Bootstrap 5.3 CDN、Font Awesome 6.4 CDN、jQuery 3.6 CDN）。各 app 专属模板位于各自的 `templates/<app_name>/` 目录。静态文件（`css/style.css`、`js/main.js`）位于项目级 `static/` 目录。

### 代码模式

- 使用函数视图 + `@login_required` 装饰器保护受限路由
- 自定义表单继承 Django 内置的 `UserCreationForm`、`AuthenticationForm`、`ModelForm`
- 分页使用 `django.core.paginator.Paginator`，每页 12 条
- AJAX 收藏切换：检测 `X-Requested-With: XMLHttpRequest` 请求头并返回 JSON
- 道具"删除"为软删除 —— 将 status 设为 `'off_shelf'` 而非删除数据库记录
- 搜索使用 `Q` 对象对 name 和 description 进行 OR 匹配，其他筛选条件通过链式 `.filter()` 叠加
- 使用 messages 框架向用户反馈操作结果（success/warning/error）
- 图片上传至 `media/` 目录（MEDIA_ROOT）
- 语言：zh-hans，时区：Asia/Shanghai

### 测试

使用 Django 的 `TestCase` 配合 `Client`。测试文件位于各 app 的 `tests.py` 中。测试数据库为内存 SQLite。通过信号机制，创建 User 时会自动创建对应的 UserProfile。当前测试覆盖：用户注册、登录、认证拦截、道具列表、道具详情（含浏览量递增）、搜索以及收藏切换。
