from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from .models import Item, Category, Favorite
from .forms import ItemForm, ItemSearchForm


def item_list(request):
    """道具列表页（分页、搜索、排序）"""
    form = ItemSearchForm(request.GET)
    items = Item.objects.filter(status='available').select_related('seller', 'category')

    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        game = form.cleaned_data.get('game')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort = form.cleaned_data.get('sort')

        if keyword:
            items = items.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))
        if game:
            items = items.filter(game=game)
        if min_price is not None:
            items = items.filter(price__gte=min_price)
        if max_price is not None:
            items = items.filter(price__lte=max_price)
        if sort:
            items = items.order_by(sort)

    # 分类筛选（通过URL参数）
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # 分页
    paginator = Paginator(items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'items/item_list.html', {
        'form': form,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_id,
    })


def item_detail(request, pk):
    """道具详情页"""
    item = get_object_or_404(Item, pk=pk)
    # 增加浏览次数
    item.views_count += 1
    item.save(update_fields=['views_count'])

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, item=item).exists()

    # 相关道具推荐（同游戏或同分类）
    related_items = Item.objects.filter(
        status='available', game=item.game
    ).exclude(pk=item.pk)[:4]

    return render(request, 'items/item_detail.html', {
        'item': item,
        'is_favorited': is_favorited,
        'related_items': related_items,
    })


@login_required
def item_create(request):
    """发布道具"""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            messages.success(request, '道具发布成功！')
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm()
    return render(request, 'items/item_form.html', {'form': form, 'title': '发布道具'})


@login_required
def item_edit(request, pk):
    """编辑道具"""
    item = get_object_or_404(Item, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '道具信息已更新。')
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'items/item_form.html', {'form': form, 'title': '编辑道具', 'item': item})


@login_required
def item_delete(request, pk):
    """删除（下架）道具"""
    item = get_object_or_404(Item, pk=pk, seller=request.user)
    if request.method == 'POST':
        item.status = 'off_shelf'
        item.save(update_fields=['status'])
        messages.success(request, '道具已下架。')
        return redirect('users:profile')
    return render(request, 'items/item_confirm_delete.html', {'item': item})


@login_required
def toggle_favorite(request, pk):
    """收藏/取消收藏"""
    item = get_object_or_404(Item, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, item=item)
    if not created:
        favorite.delete()
        is_favorited = False
        msg = '已取消收藏。'
    else:
        is_favorited = True
        msg = '已添加到收藏。'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorited': is_favorited, 'message': msg})

    messages.success(request, msg)
    return redirect('items:detail', pk=pk)


@login_required
def favorites_list(request):
    """我的收藏列表"""
    favorites = Favorite.objects.filter(user=request.user).select_related('item', 'item__seller', 'item__category')
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'items/favorites.html', {'page_obj': page_obj})


@login_required
def my_items(request):
    """我发布的道具"""
    items = Item.objects.filter(seller=request.user).order_by('-created_at')
    paginator = Paginator(items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'items/my_items.html', {'page_obj': page_obj})
