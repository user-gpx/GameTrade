from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from items.models import Item
from orders.models import Order
from payments.models import Payment
from users.models import UserProfile

from .models import TransactionLog

User = get_user_model()


ORDER_STATUS_ALIASES = {
    'pending_payment': Order.STATUS_PENDING_PAYMENT,
    'paid': Order.STATUS_PAID,
    'shipped': Order.STATUS_SHIPPED,
    'completed': Order.STATUS_COMPLETED,
    'cancelled': Order.STATUS_CANCELLED,
    'canceled': Order.STATUS_CANCELLED,
}


def _get_user_from_request(request):
    user_id = request.POST.get('user_id') or request.GET.get('user_id')
    if user_id:
        try:
            return User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError):
            pass
    if request.user.is_authenticated:
        return request.user
    return None


def _json_error(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


@csrf_exempt
@require_POST
@transaction.atomic
def buy_now(request):
    """简化购买：创建订单 + 扣款 + 支付一步完成"""
    user = _get_user_from_request(request)
    if not user:
        return _json_error('请先登录', status=401)

    item_id = request.POST.get('item_id')
    if not item_id:
        return _json_error('缺少道具ID')

    try:
        item = Item.objects.select_for_update().get(id=int(item_id))
    except (Item.DoesNotExist, ValueError):
        return _json_error('道具不存在', status=404)

    if item.status != Item.Status.ON_SALE or item.stock <= 0:
        return _json_error('道具已售罄或已下架')
    if item.seller_id == user.id:
        return _json_error('不能购买自己的道具')

    buyer_profile, _ = UserProfile.objects.select_for_update().get_or_create(user=user)
    if buyer_profile.balance < item.price:
        return _json_error(f'余额不足，当前余额 ¥{buyer_profile.balance}，需要 ¥{item.price}')

    buyer_profile.balance = Decimal(buyer_profile.balance) - Decimal(item.price)
    buyer_profile.save(update_fields=['balance'])
    TransactionLog.objects.create(
        user=user,
        amount=item.price,
        type=TransactionLog.Type.DEBIT,
        balance_after=buyer_profile.balance,
    )

    item.stock = item.stock - 1
    if item.stock == 0:
        item.status = Item.Status.SOLD
    item.save(update_fields=['stock', 'status'])

    order = Order.objects.create(
        buyer=user,
        seller=item.seller,
        item=item,
        price=item.price,
        status=Order.STATUS_PAID,
    )
    order.paid_at = timezone.now()
    order.save(update_fields=['paid_at'])

    Payment.objects.create(
        order=order,
        pay_method=request.POST.get('pay_method', 'mock'),
        pay_status=Payment.Status.SUCCESS,
        amount=item.price,
    )

    return JsonResponse({
        'ok': True,
        'order_id': order.id,
        'status': order.status,
        'balance': str(buyer_profile.balance),
    })


@csrf_exempt
@require_POST
@transaction.atomic
def create_order(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    item_id = request.POST.get('item_id')
    if not item_id:
        return _json_error('missing item_id')

    try:
        item = Item.objects.select_for_update().get(id=int(item_id))
    except (Item.DoesNotExist, ValueError):
        return _json_error('item not found', status=404)

    if item.status != Item.Status.ON_SALE or item.stock <= 0:
        return _json_error('item not available')
    if item.seller_id == user.id:
        return _json_error('cannot buy your own item')

    item.status = Item.Status.LOCKED
    item.stock = item.stock - 1
    item.save(update_fields=['status', 'stock'])

    order = Order.objects.create(
        buyer=user,
        seller=item.seller,
        item=item,
        price=item.price,
        status=Order.STATUS_PENDING_PAYMENT,
    )

    return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status})


@csrf_exempt
@require_POST
@transaction.atomic
def cancel_order(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    order_id = request.POST.get('order_id')
    if not order_id:
        return _json_error('missing order_id')

    try:
        order = Order.objects.select_for_update().get(id=int(order_id))
    except (Order.DoesNotExist, ValueError):
        return _json_error('order not found', status=404)

    if order.buyer_id != user.id:
        return _json_error('forbidden', status=403)
    if order.status != Order.STATUS_PENDING_PAYMENT:
        return _json_error('order not cancelable')

    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=['status'])

    item = Item.objects.select_for_update().get(id=order.item_id)
    item.stock = item.stock + 1
    item.status = Item.Status.ON_SALE
    item.save(update_fields=['stock', 'status'])

    return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status})


@csrf_exempt
@require_POST
@transaction.atomic
def initiate_payment(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    order_id = request.POST.get('order_id')
    pay_method = request.POST.get('pay_method', 'mock')
    if not order_id:
        return _json_error('missing order_id')

    try:
        order = Order.objects.select_for_update().get(id=int(order_id))
    except (Order.DoesNotExist, ValueError):
        return _json_error('order not found', status=404)

    if order.buyer_id != user.id:
        return _json_error('forbidden', status=403)
    if order.status != Order.STATUS_PENDING_PAYMENT:
        return _json_error('order not payable')

    payment, _ = Payment.objects.get_or_create(order=order)
    payment.pay_method = pay_method
    payment.save(update_fields=['pay_method'])

    return JsonResponse({'ok': True, 'payment_no': payment.payment_no, 'pay_status': payment.pay_status})


@csrf_exempt
@require_POST
@transaction.atomic
def payment_callback(request):
    payment_no = request.POST.get('payment_no')
    result = request.POST.get('result', 'success')
    if not payment_no:
        return _json_error('missing payment_no')

    try:
        payment = Payment.objects.select_for_update().select_related('order').get(payment_no=payment_no)
    except Payment.DoesNotExist:
        return _json_error('payment not found', status=404)

    order = payment.order

    if order.status != Order.STATUS_PENDING_PAYMENT:
        return _json_error('order not in pending_payment')

    if result == 'success':
        payment.mark_success()
        order.mark_paid()

        item = Item.objects.select_for_update().get(id=order.item_id)
        item.status = Item.Status.SOLD
        item.save(update_fields=['status'])
        return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status})

    payment.mark_failed()
    return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status, 'pay_status': payment.pay_status})


@csrf_exempt
@require_POST
@transaction.atomic
def ship_order(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    order_id = request.POST.get('order_id')
    if not order_id:
        return _json_error('missing order_id')

    try:
        order = Order.objects.select_for_update().get(id=int(order_id))
    except (Order.DoesNotExist, ValueError):
        return _json_error('order not found', status=404)

    if order.seller_id != user.id:
        return _json_error('forbidden', status=403)
    if order.status != Order.STATUS_PAID:
        return _json_error('order not shippable')

    shipping_info = request.POST.get('shipping_info', '交易接口发货')
    order.mark_shipped(shipping_info)
    return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status})


@csrf_exempt
@require_POST
@transaction.atomic
def confirm_receipt(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    order_id = request.POST.get('order_id')
    if not order_id:
        return _json_error('missing order_id')

    try:
        order = Order.objects.select_for_update().get(id=int(order_id))
    except (Order.DoesNotExist, ValueError):
        return _json_error('order not found', status=404)

    if order.buyer_id != user.id:
        return _json_error('forbidden', status=403)
    if order.status != Order.STATUS_SHIPPED:
        return _json_error('order not confirmable')

    seller_profile, _ = UserProfile.objects.select_for_update().get_or_create(user_id=order.seller_id)
    seller_profile.balance = Decimal(seller_profile.balance) + Decimal(order.price)
    seller_profile.save(update_fields=['balance'])
    TransactionLog.objects.create(
        user_id=order.seller_id,
        amount=order.price,
        type=TransactionLog.Type.CREDIT,
        balance_after=seller_profile.balance,
    )

    order.mark_completed()

    return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status, 'seller_balance': str(seller_profile.balance)})


@csrf_exempt
def buyer_orders(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    status = ORDER_STATUS_ALIASES.get(request.GET.get('status'), request.GET.get('status'))
    qs = Order.objects.filter(buyer_id=user.id).select_related('item').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)

    data = []
    for o in qs[:200]:
        data.append(
            {
                'id': o.id,
                'buyer_id': o.buyer_id,
                'seller_id': o.seller_id,
                'item_id': o.item_id,
                'price': str(o.price),
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
        )

    return JsonResponse({'ok': True, 'orders': data})


@csrf_exempt
def seller_orders(request):
    user = _get_user_from_request(request)
    if not user:
        return _json_error('invalid user', status=401)

    status = ORDER_STATUS_ALIASES.get(request.GET.get('status'), request.GET.get('status'))
    qs = Order.objects.filter(seller_id=user.id).select_related('item').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)

    data = []
    for o in qs[:200]:
        data.append(
            {
                'id': o.id,
                'buyer_id': o.buyer_id,
                'seller_id': o.seller_id,
                'item_id': o.item_id,
                'price': str(o.price),
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
        )

    return JsonResponse({'ok': True, 'orders': data})


@csrf_exempt
@require_POST
@transaction.atomic
def recharge(request):
    """模拟充值：默认充值100元"""
    user = _get_user_from_request(request)
    if not user:
        return _json_error('请先登录', status=401)
    amount = Decimal(request.POST.get('amount', '100'))
    profile, _ = UserProfile.objects.select_for_update().get_or_create(user=user)
    profile.balance = Decimal(profile.balance) + amount
    profile.save(update_fields=['balance'])
    TransactionLog.objects.create(
        user=user,
        amount=amount,
        type=TransactionLog.Type.CREDIT,
        balance_after=profile.balance,
    )
    return JsonResponse({'ok': True, 'balance': str(profile.balance), 'amount': str(amount)})


@login_required
def buyer_order_page(request):
    """买家订单页面"""
    orders = Order.objects.filter(buyer=request.user).select_related('item', 'seller').order_by('-created_at')
    return render(request, 'trading/buyer_orders.html', {'orders': orders})


@login_required
def seller_order_page(request):
    """卖家订单页面"""
    orders = Order.objects.filter(seller=request.user).select_related('item', 'buyer').order_by('-created_at')
    return render(request, 'trading/seller_orders.html', {'orders': orders})
