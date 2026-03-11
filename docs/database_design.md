# 数据库设计文档

## 用户表 (users_user)
- id: 主键
- username: 用户名
- password: 密码
- email: 邮箱
- phone: 手机号
- balance: 余额
- avatar: 头像
- date_joined: 注册时间

## 道具表 (items_gameitem)
- id: 主键
- name: 道具名称
- category: 分类
- price: 价格
- seller_id: 卖家ID
- status: 状态
- image: 图片
- created_at: 发布时间

## 订单表 (orders_order)
- id: 主键
- order_no: 订单号
- buyer_id: 买家ID
- seller_id: 卖家ID
- item_id: 道具ID
- price: 成交价
- status: 状态
- created_at: 创建时间