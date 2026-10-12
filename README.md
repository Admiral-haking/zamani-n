# zamani-n

## راه‌اندازی production روی Vercel و Neon

1. در Neon رمز دیتابیس را Rotate کنید؛ رمز قبلی که افشا شده قابل استفاده نیست.
2. در Vercel از مسیر `Settings → Environment Variables` مقدار جدید `DATABASE_URL` را برای محیط `Production` اضافه کنید.
3. این متغیرها را نیز تنظیم کنید: `DJANGO_SECRET_KEY`، `DJANGO_DEBUG=False` و `DJANGO_ALLOWED_HOSTS=.vercel.app`.
4. یک Redeploy جدید انجام دهید.
5. روی سیستم محلی، با همان `DATABASE_URL` جدید، migrationها را اجرا کنید:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://...'
export DJANGO_SECRET_KEY='...'
export DJANGO_DEBUG=False
python manage.py migrate
python manage.py createsuperuser
```

سایت از `/`، API از `/api/`، مستندات از `/api/docs/` و پنل از `/admin/` ارائه می‌شوند. فایل‌های آپلودی در Vercel دائمی نیستند و برای آن‌ها باید object storage جداگانه تنظیم شود.
