from calendar import monthrange

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import get_connection, send_mail
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from items.models import Favorite, Item
from orders.models import Order
from .models import MonthlyReport


def _month_bounds(year, month):
    start = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
    end_day = monthrange(year, month)[1]
    end = timezone.datetime(year, month, end_day, 23, 59, 59, tzinfo=timezone.get_current_timezone())
    return start, end


def _build_report_content(user, year, month):
    start, end = _month_bounds(year, month)
    completed_orders = Order.objects.filter(
        status=Order.STATUS_COMPLETED,
        completed_at__range=(start, end),
    )
    user_related_orders = completed_orders.filter(buyer=user) | completed_orders.filter(seller=user)
    new_items = Item.objects.filter(created_at__range=(start, end))
    favorite_items = Favorite.objects.filter(user=user).select_related('item', 'item__seller')[:8]

    hot_items = (
        completed_orders.values('item__name')
        .annotate(order_count=Count('id'), amount=Sum('price'))
        .order_by('-order_count', '-amount')[:5]
    )
    followed_hot = (
        Favorite.objects.values('item__name')
        .annotate(favorite_count=Count('id'))
        .order_by('-favorite_count')[:5]
    )

    lines = [
        f'{year}年{month}月交易月报',
        f'本月平台完成订单：{completed_orders.count()} 笔',
        f'本月平台交易金额：{completed_orders.aggregate(total=Sum("price"))["total"] or 0} 元',
        f'与你相关的完成订单：{user_related_orders.distinct().count()} 笔',
        f'本月新上架道具：{new_items.count()} 件',
        '',
        '热门成交道具：',
    ]
    lines += [
        f'{idx}. {row["item__name"]}，成交 {row["order_count"]} 次，金额 {row["amount"] or 0} 元'
        for idx, row in enumerate(hot_items, start=1)
    ] or ['暂无成交数据']
    lines.append('')
    lines.append('收藏热度排行：')
    lines += [
        f'{idx}. {row["item__name"]}，被收藏 {row["favorite_count"]} 次'
        for idx, row in enumerate(followed_hot, start=1)
    ] or ['暂无收藏数据']
    lines.append('')
    lines.append('你关注的道具：')
    lines += [
        f'- {fav.item.name}：{fav.item.get_status_display()}，卖家 {fav.item.seller.username}，价格 {fav.item.price} 元'
        for fav in favorite_items
    ] or ['你暂时还没有收藏道具']
    return '\n'.join(lines)


@login_required
def dashboard(request):
    now = timezone.localtime()
    my_buy_count = Order.objects.filter(buyer=request.user).count()
    my_sell_count = Order.objects.filter(seller=request.user).count()
    pending_ship_count = Order.objects.filter(seller=request.user, status=Order.STATUS_PAID).count()
    pending_receive_count = Order.objects.filter(buyer=request.user, status=Order.STATUS_SHIPPED).count()
    latest_orders = Order.objects.filter(buyer=request.user) | Order.objects.filter(seller=request.user)

    return render(request, 'stats/dashboard.html', {
        'my_buy_count': my_buy_count,
        'my_sell_count': my_sell_count,
        'pending_ship_count': pending_ship_count,
        'pending_receive_count': pending_receive_count,
        'latest_orders': latest_orders.distinct().select_related('item', 'buyer', 'seller')[:8],
        'current_year': now.year,
        'current_month': now.month,
        'active_my_menu': 'stats',
    })


@login_required
def monthly_report(request):
    now = timezone.localtime()
    year = int(request.GET.get('year') or now.year)
    month = int(request.GET.get('month') or now.month)

    if request.method == 'POST':
        year = int(request.POST.get('year') or now.year)
        month = int(request.POST.get('month') or now.month)
        content = _build_report_content(request.user, year, month)
        report, _ = MonthlyReport.objects.update_or_create(
            user=request.user,
            year=year,
            month=month,
            defaults={'content': content},
        )
        messages.success(request, '月报已生成。')
        return redirect('stats:monthly_report_detail', pk=report.pk)

    reports = MonthlyReport.objects.filter(user=request.user)
    return render(request, 'stats/monthly_report.html', {
        'reports': reports,
        'year': year,
        'month': month,
        'active_my_menu': 'stats',
    })


@login_required
def monthly_report_detail(request, pk):
    report = get_object_or_404(MonthlyReport, pk=pk, user=request.user)
    return render(request, 'stats/monthly_report_detail.html', {
        'report': report,
        'active_my_menu': 'stats',
    })


@login_required
def send_report_email(request, pk):
    report = get_object_or_404(MonthlyReport, pk=pk, user=request.user)
    if request.method == 'POST':
        if not request.user.email:
            messages.warning(request, '你的账号还没有邮箱，暂时不能发送月报。')
        else:
            connection = get_connection('django.core.mail.backends.console.EmailBackend')
            send_mail(
                subject=f'{report.year}年{report.month}月游戏道具交易月报',
                message=report.content,
                from_email=None,
                recipient_list=[request.user.email],
                connection=connection,
                fail_silently=False,
            )
            report.emailed_at = timezone.now()
            report.save(update_fields=['emailed_at'])
            messages.success(request, '月报邮件已发送。')
    return redirect('stats:monthly_report_detail', pk=report.pk)
