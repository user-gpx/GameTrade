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

### 项目分工

成员A：用户认证 + 道具展示模块
核心任务：

用户注册、登录、登出、个人资料修改（含头像上传）。

道具模型设计（名称、分类、价格、图片、描述等）。

道具列表页（分页、排序、简单搜索）。

道具详情页（显示信息、收藏按钮）。

收藏/关注功能（道具收藏、关注列表）。

具体产出：

用户相关页面（登录/注册/个人中心）的HTML模板。

道具列表、详情页面的HTML模板。

相关视图函数/类、URL配置。

数据库迁移脚本。

单元测试（用户登录、道具浏览）。

协作点：

与成员B确定道具模型字段（尤其是价格、卖家外键）的最终定义。

与成员C沟通页面整体样式（Bootstrap主题），确保风格统一。

成员B：交易模块 + 支付系统
核心任务：

订单模型设计（状态机、关联道具和买卖双方）。

购买流程：点击购买 → 创建订单（锁定道具） → 跳转支付。

卖家发货功能：卖家填写物流/发货信息，变更订单状态。

买家确认收货功能：完成交易，更新卖家余额。

支付集成（模拟支付或支付宝沙箱），处理支付回调。

资金账户：在用户模型中添加余额字段，充值功能（可选）。

具体产出：

订单相关页面（订单确认页、支付页、发货页、确认收货页）。

支付回调处理逻辑（异步通知、签名验证）。

用户余额变动记录（可设计一个交易流水表）。

单元测试（订单状态流转、支付回调）。

协作点：

与成员A对接道具信息（确保道具价格能传递到订单）。

与成员C协调订单管理页面所需的数据接口。

成员C：订单管理 + 统计功能 + 前端整合
核心任务：

买家订单列表（按状态筛选，显示操作按钮）。

卖家订单列表（按状态筛选，显示发货操作）。

订单详情页（展示完整订单信息）。

统计模块：定时生成月报（使用Django的定时任务或Celery），统计热门道具、用户关注等。

邮件发送功能：将月报发送给用户（可手动触发演示）。

前端整体美化：统一所有页面的Bootstrap样式，调整布局，确保响应式。

项目整合：协调三人代码合并，解决冲突，维护Git仓库。

具体产出：

买家/卖家订单列表、详情页面。

月报生成脚本（可手动触发演示），邮件发送逻辑。

全局基础模板（base.html），集成Bootstrap和公共导航栏。

编写项目文档（README、部署说明）。

协助成员A和B进行界面调整。

协作点：

需要获取成员B的订单数据，成员A的道具数据。

协调各模块的URL命名规范，避免冲突。

协作流程与时间安排
第1-2周（需求分析、设计）：

三人共同讨论数据库设计，确定模型关系。

搭建Django项目框架，创建Git仓库，制定代码规范。

成员A负责用户认证模块原型，成员B设计订单模型，成员C搭建基础模板和静态文件。

第3-10周（并行开发）：

每周进行1-2次短会，同步进度，协调接口。

成员A完成用户认证和道具展示。

成员B完成交易核心和支付模拟。

成员C完成订单管理页面，并开始统计模块开发。

成员C定期合并代码，解决冲突，保持主分支可运行。

第11-12周（联调与美化）：

三人一起测试完整流程（注册→登录→发布道具→购买→支付→发货→确认收货→查看订单→收到月报）。

成员C统一调整UI细节，成员A和B配合修复bug。

编写单元测试，覆盖核心功能。

第13-14周（文档与报告）：

每人撰写自己所负责模块的技术文档（数据库设计、关键代码说明）。

成员C整合形成完整的课程设计报告。

准备演示视频、PPT。

第15周（答辩）：

模拟答辩，完善演示流程。