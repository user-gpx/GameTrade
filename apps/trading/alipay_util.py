from alipay import AliPay, AliPayConfig
from django.conf import settings


def get_alipay_client():
    """初始化支付宝沙箱客户端"""
    with open(settings.ALIPAY_APP_PRIVATE_KEY_PATH) as f:
        app_private_key = f.read()
    with open(settings.ALIPAY_PUBLIC_KEY_PATH) as f:
        alipay_public_key = f.read()

    return AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=None,
        app_private_key_string=app_private_key,
        alipay_public_key_string=alipay_public_key,
        sign_type='RSA2',
        debug=settings.DEBUG,
        config=AliPayConfig(timeout=15),
    )
