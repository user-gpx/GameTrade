from django import forms
from .models import Item


class ItemForm(forms.ModelForm):
    """道具发布/编辑表单"""
    class Meta:
        model = Item
        fields = ['name', 'category', 'game', 'price', 'description', 'image']
        labels = {
            'name': '道具名称',
            'category': '分类',
            'game': '所属游戏',
            'price': '价格（元）',
            'description': '描述',
            'image': '道具图片',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入道具名称'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'game': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入价格', 'min': '0.01', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '请详细描述道具信息'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('价格必须大于0')
        return price


class ItemSearchForm(forms.Form):
    """道具搜索表单"""
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜索道具名称...',
        }),
        label='关键词'
    )
    game = forms.ChoiceField(
        required=False,
        choices=[('', '所有游戏')] + Item.GAME_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='游戏'
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '最低价', 'min': '0', 'step': '0.01'}),
        label='最低价'
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '最高价', 'min': '0', 'step': '0.01'}),
        label='最高价'
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', '最新发布'),
            ('price', '价格从低到高'),
            ('-price', '价格从高到低'),
            ('-views_count', '最多浏览'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='排序'
    )
