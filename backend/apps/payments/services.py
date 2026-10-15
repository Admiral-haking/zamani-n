# backend/apps/payments/services.py
"""
سرویس اتصال به درگاه پرداخت زرین‌پال (API نسخه ۴)
برای پرداخت آنلاین مشتریان هنگام تسویه سبد خرید.
"""

import requests

from django.conf import settings


class ZarinpalService:
    """کلاینت ساده زرین‌پال با پشتیبانی از حالت تست (Sandbox)"""

    @staticmethod
    def _gate_base() -> str:
        if settings.ZARINPAL_SANDBOX:
            return "https://sandbox.zarinpal.com"
        return "https://payment.zarinpal.com"

    @staticmethod
    def _headers():
        return {"Content-Type": "application/json", "Accept": "application/json"}

    @classmethod
    def request_payment(cls, amount: int, description: str, email=None, mobile=None):
        """درخواست شروع پرداخت. در صورت موفقیت (authority, payment_url) و در خطا (None, None)"""
        url = f"{cls._gate_base()}/pg/v4/payment/request.json"
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": int(amount),
            "callback_url": settings.ZARINPAL_CALLBACK_URL,
            "description": description[:255] if description else "خرید از فروشگاه زمانی",
        }
        metadata = {}
        if email:
            metadata["email"] = email
        if mobile:
            metadata["mobile"] = mobile
        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(url, json=payload, headers=cls._headers(), timeout=15)
            data = response.json() or {}
        except Exception as e:
            return None, f"خطا در ارتباط با درگاه پرداخت: {e}"

        result = data.get("data") or {}
        errors = data.get("errors") or {}

        if result.get("code") == 100 and result.get("authority"):
            return result["authority"], cls.payment_url(result["authority"])

        code = result.get("code", errors.get("code", "unknown"))
        message = result.get("message", errors.get("message", "خطا در ارتباط با درگاه پرداخت"))
        return None, f"{code} - {message}"

    @staticmethod
    def payment_url(authority: str) -> str:
        return f"{ZarinpalService._gate_base()}/pg/StartPay/{authority}"

    @classmethod
    def verify_payment(cls, authority: str, amount: int):
        """تأیید نهایی پرداخت. (success, ref_id, message)"""
        url = f"{cls._gate_base()}/pg/v4/payment/verify.json"
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": int(amount),
            "authority": authority,
        }

        try:
            response = requests.post(url, json=payload, headers=cls._headers(), timeout=20)
            data = response.json() or {}
        except Exception:
            return False, None, "خطا در ارتباط با درگاه پرداخت"

        result = data.get("data") or {}
        errors = data.get("errors") or {}

        if result.get("code") == 100 and result.get("ref_id"):
            return True, result["ref_id"], None

        code = result.get("code", errors.get("code", "unknown"))
        message = result.get("message", errors.get("message", "پرداخت تأیید نشد"))
        return False, None, f"{code} - {message}"