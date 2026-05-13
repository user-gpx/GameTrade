from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UserForm, ProfileForm


def user_register(request):
    """用户注册"""
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功，欢迎加入！')
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    """用户登出"""
    logout(request)
    messages.success(request, '您已成功退出登录。')
    return redirect('/')


@login_required
def user_profile(request):
    """查看个人资料"""
    profile = request.user.profile
    # 获取该用户发布的道具（如果items app已有模型）
    user_items = []
    try:
        from items.models import Item
        user_items = Item.objects.filter(seller=request.user).order_by('-created_at')[:6]
    except Exception:
        pass
    return render(request, 'users/profile.html', {
        'profile': profile,
        'user_items': user_items,
    })


@login_required
def edit_profile(request):
    """编辑个人资料"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '个人资料已更新。')
            return redirect('users:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'users/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })
