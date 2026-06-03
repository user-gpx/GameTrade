# GameTrade 游戏道具交易平台

GameTrade 是一个基于 Django 的游戏道具交易平台课程设计项目，面向游戏玩家提供道具浏览、发布、收藏、购买、出售、订单管理、模拟支付和交易统计月报等功能。

## 功能模块

| 模块 | 职责 |
|---|---|
| `users` | 用户注册、登录、退出、个人资料、头像上传、账户余额 |
| `items` | 道具发布、道具展示、搜索筛选、详情页、收藏 |
| `orders` | 统一订单模型、订单状态流转、买家订单、卖家订单、支付/发货/确认收货页面 |
| `payments` | 支付记录、模拟支付状态 |
| `trading` | 交易 API、充值、资金流水，复用 `orders.Order` |
| `stats` | 交易月报、热门道具统计、关注道具统计、月报邮件发送 |

## 核心流程

### 购买流程

1. 买家登录系统，浏览道具。
2. 买家选择道具并创建订单。
3. 买家完成模拟支付，订单进入待发货状态。
4. 卖家填写发货信息，订单进入待收货状态。
5. 买家确认收货，订单完成。

### 销售流程

1. 卖家登录系统，发布道具并设置价格。
2. 买家购买并支付后，订单显示在卖家订单列表。
3. 卖家发货。
4. 买家确认收货后，交易完成。

## 模块边界约定

订单数据统一使用：

```python
from orders.models import Order
```

道具数据统一使用：

```python
from items.models import Item
```

用户数据统一使用：

```python
from django.contrib.auth.models import User
```

`orders` 是订单主模块，`trading` 不再创建第二套订单模型，只作为交易 API 和资金流水辅助模块复用 `orders.Order`。

## 订单状态

| 状态常量 | 数据库存储值 | 页面含义 |
|---|---|---|
| `Order.STATUS_PENDING_PAYMENT` | `pending_payment` | 待支付 |
| `Order.STATUS_PAID` | `paid` | 待发货 |
| `Order.STATUS_SHIPPED` | `shipped` | 待收货 |
| `Order.STATUS_COMPLETED` | `completed` | 已完成 |
| `Order.STATUS_CANCELLED` | `cancelled` | 已取消 |

订单状态流转：

```text
pending_payment -> paid -> shipped -> completed
```

## 运行环境

推荐使用 Python 3.10。

```bash
conda create -n gametrade python=3.10 -y
conda activate gametrade
pip install -r requirements.txt
```

## 初始化数据库

```bash
python manage.py migrate
```

如需创建管理员：

```bash
python manage.py createsuperuser
```

## 启动项目

```bash
python manage.py runserver
```

访问地址：

```text
http://127.0.0.1:8000/
```

## 演示账号

| 用户名 | 密码 | 说明 |
|---|---|---|
| `zy` | `z1236547` | 演示账号，已有买入/卖出订单数据 |

常用页面：

| 页面 | 地址 |
|---|---|
| 首页 | `/` |
| 道具列表 | `/items/` |
| 发布道具 | `/items/sell/` |
| 我的 | `/users/profile/` |
| 买家订单 | `/orders/buyer/` |
| 卖家订单 | `/orders/seller/` |
| 统计中心 | `/stats/` |
| 交易月报 | `/stats/reports/monthly/` |

## 测试

系统检查：

```bash
python manage.py check
```

运行主要模块测试：

```bash
python manage.py test users items orders stats trading payments
```

当前主要模块测试覆盖：

- 用户注册、登录、个人资料
- 道具浏览、收藏
- 订单创建、支付、发货、确认收货
- 交易 API 流程
- 月报生成

## Selenium Web UI 测试

Java Selenium 测试项目位于：

```text
B:\JAVACODE\demo
```

运行前先启动 Django：

```bash
python manage.py runserver
```

然后在 Java 测试项目目录运行：

```bash
mvn test
```

测试内容包括：

- 登录 `zy`
- 点击右上角“我的”
- 验证个人中心左侧菜单
- 验证买家订单与卖家订单列表
- 验证订单状态筛选
- 验证交易月报页面

## 项目结构

```text
GameTrade/
├── apps/
│   ├── users/
│   ├── items/
│   ├── orders/
│   ├── payments/
│   ├── trading/
│   └── stats/
├── config/
├── templates/
├── static/
├── media/
├── manage.py
└── requirements.txt
```

## 说明

同一个浏览器的多个标签页会共享登录状态，这是 Django Session/Cookie 的正常机制。测试多个账号时，建议使用不同浏览器、无痕窗口，或分别访问 `127.0.0.1` 和 `localhost`。
