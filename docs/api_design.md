# API接口文档

## 用户相关
- POST /api/users/register/ - 注册
- POST /api/users/login/ - 登录
- GET /api/users/profile/ - 获取个人信息

## 道具相关
- GET /api/items/ - 获取道具列表
- GET /api/items/{id}/ - 获取道具详情
- POST /api/items/ - 发布道具
- PUT /api/items/{id}/ - 更新道具

## 订单相关
- GET /api/orders/buyer/ - 买家订单列表
- GET /api/orders/seller/ - 卖家订单列表
- POST /api/orders/ - 创建订单
- PUT /api/orders/{id}/ship/ - 发货
- PUT /api/orders/{id}/confirm/ - 确认收货