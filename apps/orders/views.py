from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from items.models import Item
from .forms import ShippingForm
from .models import Order


def _paginate(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))


def _filter_status(request, queryset):
    status = request.GET.get('status', '').strip()
    if status:
        queryset = queryset.filter(status=status)
    return queryset, status


@login_required
def create_order(request, item_id):
    item = get_object_or_404(Item, pk=item_id, status='available')
    if item.seller == request.user:
        messages.warning(request, '不能购买自己发布的道具。')
        return redirect('items:detail', pk=item.pk)

    order, created = Order.objects.get_or_create(
        item=item,
        buyer=request.user,
        status=Order.STATUS_PENDING_PAYMENT,
        defaults={'seller': item.seller, 'price': item.price},
    )
    if created:
        messages.success(request, '订单已创建，请继续完成支付。')
    return redirect('orders:detail', pk=order.pk)


@login_required
def buyer_orders(request):
    orders, current_status = _filter_status(
        request,
        Order.objects.filter(buyer=request.user).select_related('item', 'seller'),
    )
    return render(request, 'orders/order_list.html', {
        'page_obj': _paginate(request, orders),
        'current_status': current_status,
        'status_choices': Order.STATUS_CHOICES,
        'list_type': 'buyer',
        'title': '我的购买订单',
        'active_my_menu': 'buyer_orders',
    })


@login_required
def seller_orders(request):
    orders, current_status = _filter_status(
        request,
        Order.objects.filter(seller=request.user).select_related('item', 'buyer'),
    )
    return render(request, 'orders/order_list.html', {
        'page_obj': _paginate(request, orders),
        'current_status': current_status,
        'status_choices': Order.STATUS_CHOICES,
        'list_type': 'seller',
        'title': '我的出售订单',
        'active_my_menu': 'seller_orders',
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('item', 'buyer', 'seller'), pk=pk)
    if request.user not in [order.buyer, order.seller]:
        messages.error(request, '你无权查看该订单。')
        return redirect('orders:buyer_orders')
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def pay_order(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user, status=Order.STATUS_PENDING_PAYMENT)
    if request.method == 'POST':
        order.mark_paid()
        messages.success(request, '模拟支付成功，系统已通知卖家发货。')
        return redirect('orders:detail', pk=order.pk)
    return render(request, 'orders/pay_order.html', {'order': order})


@login_required
def ship_order(request, pk):
    order = get_object_or_404(Order, pk=pk, seller=request.user, status=Order.STATUS_PAID)
    form = ShippingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        order.mark_shipped(form.cleaned_data['shipping_info'])
        messages.success(request, '发货信息已提交，等待买家确认收货。')
        return redirect('orders:detail', pk=order.pk)
    return render(request, 'orders/ship_order.html', {'order': order, 'form': form})


@login_required
def confirm_receive(request, pk):
    order = get_object_or_404(Order, pk=pk, buyer=request.user, status=Order.STATUS_SHIPPED)
    if request.method == 'POST':
        order.mark_completed()
        messages.success(request, '已确认收货，交易完成。')
        return redirect('orders:detail', pk=order.pk)
    return render(request, 'orders/confirm_receive.html', {'order': order})
