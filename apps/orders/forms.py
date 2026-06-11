from django import forms


class ShippingForm(forms.Form):
    shipping_info = forms.CharField(
        label='发货信息',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '请输入物流公司、单号或游戏内交付说明',
        }),
        min_length=5,
    )
