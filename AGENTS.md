# AGENTS.md — حافظه پروژه ZAMANI (برای دستیار opencode)

> این فایل را در شروع هر جلسه جدی بخوان. آخرین به‌روزرسانی: 2026-08-26

## ۱) پروژه چیست؟
سامانه فروش و پخش B2B یک **شرکت تولید محصولات گوشتی** (ZAMANI API).
بک‌اند: Django 6 + DRF + JWT + drf-spectacular، دیتابیس PostgreSQL.
منطق کلیدی کسب‌وکار (نیاز کارفرما):
- ۴ نقش: ادمین کل (تک‌نفر)، منشی، پخش‌کننده، مشتری
- منشی/ادمین محصول را با `base_price` ثبت می‌کنند؛ هر پخش‌کننده برای پنل خودش قیمت جدا می‌گذارد (`DistributorPrice`) → «هر پخش‌کننده مغازه خودش»
- قیمت مؤثر محصول = قیمت پخش‌کننده معرفِ مشتری، وگرنه fallback به `base_price`
- ثبت‌نام آزاد وجود ندارد؛ حساب‌ها فقط توسط ادمین/منشی یا پخش‌کننده (برای مشتریانش) ساخته می‌شوند
- ناشناس با تیکت (`POST /api/tickets/guest-request/`) درخواست حساب می‌دهد؛ ادمین تایید می‌کند → مشتریِ بدون معرف زیرمجموعه ادمین کل
- دیدن محصولات/قیمت‌ها فقط با لاگین

## ۲) محیط اجرا (مهم!)
- OS: EndeavourOS (Arch)، شل zsh | مسیر پروژه: `/home/nimux/Documents/X`
- venv سالم: `backend/venv` (Python 3.14). venv قدیمی ویندوزی حذف شده.
- **PostgreSQL فقط از Docker**: کانتینر `zamani-db` (postgres:16-alpine)، volume `zamani_pgdata`، پورت 5432، db/user=`zamani` pass=`Zm#2026!pg`. پکیج native postgresql با glibc سیستم (2.43 < 2.44) ناسازگار است — نصب مجدد نکن!
- تنظیمات DB از `backend/.env` خوانده می‌شود (لودر دستی در settings.py؛ python-dotenv نصب نیست)
- اجرای سرور (الگو تست‌شده): داخل backend:
  `setsid venv/bin/python -u manage.py runserver 0.0.0.0:8000 --noreload > logs/runserver.log 2>&1 < /dev/null & disown`
  سپس `curl http://127.0.0.1:8000/api/docs/` باید 200 بدهد.
- ⚠️ `pkill -f runserver` گاهی شل ابزار را هنگ می‌کند؛ به‌جایش: `kill $(pgrep -f "manage.py runserver" | head -1)`

## ۳) حساب‌ها و رمزها (دیتابیس فعلی PG — داده seed تازه)
| نقش | یوزر | پسورد |
|---|---|---|
| ادمین کل | admin | Admin@1404 |
| منشی | secretary | Sec@1404 |
| پخش‌کننده ۱ | distributor | Dist@1404 |
| مشتری معرفی‌شده توسط dist1 | customer1 | Cust@1404 |
| مشتری ۲ | customer2 | Cust2@1404 |
| ساخته‌شده در تست‌ها: dist2/Dist2@1404، shop_of_dist1/Cust@1404، shop_of_dist2/Cust@1404، rezaei/Reza@1404 |

رمز sudo کاربر اگر خواست: کارفرما قبلاً داده (در تاریخ چت هست) — دوباره نخواه.

## ۴) نقشه کد (تغییرات اخیر)
- `apps/pricing/models.py` → مدل جدید `DistributorPrice` (+ migration 0002). مدل قدیمی `ProductPrice` فقط read-only نگه داشته شده (`LegacyProductPriceViewSet` روی `/api/pricing/legacy/`)
- `apps/pricing/services.py` → `get_product_price(customer, product)` منطق fallback
- `apps/products/serializers/product_serializer.py` → `effective_price` + ماسک کردن base_price برای غیرمدیرها
- `apps/accounts/views/auth_views.py` → register حذف شد؛ `CreateDistributorView / CreateSecretaryView(فقط ادمین) / CreateCustomerByStaffView` روی `/api/accounts/users/create-*/`
- `apps/customers/distributor_serializers.py` → ساخت اتمیک User+Customer توسط پخش‌کننده (username/password الزامی)
- `apps/tickets/views.py` → اکشن عمومی `guest-request` (AllowAny) + Ticket.user nullable و guest_name/guest_phone (migration 0003)
- `apps/owner/views/account_requests.py` + urls → صف و approve درخواست حساب توسط ادمین
- سیگنال `apps/accounts/signals.py` → ساخت خودکار Customer/DistributorProfile بعد از ساخت User (با `_unique_phone` برای جلوگیری از تداخل phone یکتا)

## ۵) باگ‌های رفع‌شده (تکرار نکن / الگو بگیر)
۱۳ باگ اصلی: نبود پروفایل بعد از ثبت‌نام، `soft_delete` ناموجود، فیلد `Customer.distributor` غایب (migration 0004 customers)، مرده بودن `create_order_from_cart` (حالا `POST /api/orders/create_from_cart/`)، Type های ناموجود مالی (ORDER_DEBT/PAYMENT)، نشتی debtors/audit، پرداخت روی سفارش دیگران، گزارش‌های بدون route (ViewSet شدند)، cash_check بدون اثر بر مانده، پراپرتی‌های total_orders/total_spent خراب.
Race conditions: cart/balance با F() اتمیک، approve با select_for_update+atomic، کسر موجودی شرطی `quantity__gte`. همه روی PG re-test شده (۸ همزمانی سبد=۸، oversell صفر، ۵ تایید=۱ تراکنش).

## ۶) دام‌های کشف‌شده (دوباره گیر نده!)
- متد `get_permissions()` ویوست **روی** `permission_classes` اکشن اولویت دارد — برای اکشن AllowAny باید داخل get_permissions هم هندل شود (تیکت مهمان همینجا گیر کرد)
- DefaultRouter با پیشوند خالی `""`: پیشوندهای دیگر را **قبل از** آن register کن تا الگوی `(?P<pk>)` مسیرها را ندزدد (باگ POST /distributors/customers/)
- فیلدهای `decimal_places=0` (مثل Payment.amount): در JSON عدد صحیح بفرست، `"640000.00"` خطا می‌دهد
- `select_for_update` روی SQLite بی‌اثر است؛ روی PG واقعی است
- status سفارش UPPERCASE است ('DELIVERED')؛ چند جای کد قبلاً lowercase داشت

## ۷) وضعیت گیت
- branch: main | کامیت‌ها: `136838f` (وضعیت پایه بعد از ۱۳ فیکس + PG) و `54defb6` (انطباق با نیاز کارفرما)
- `.gitignore` ریشه: .env، venv، db.sqlite3، logs، media
- بکاپ SQLite قدیمی: `database/backup/db_20260824_231927.sqlite3`

## ۸) کارهای باز / تصمیمات معلق
1. **«خرید منفی» منشی مبهم است** — طبق نظر کاربر فعلاً پیاده نشود؛ از کارفرما بپرس
2. هاردنینگ production: SECRET_KEY هاردکد، DEBUG=True، CORS_ALLOW_ALL_ORIGINS=True → باید از env بیایند
3. اپ‌های خالی/بی‌استفاده: cms، forms، services، employees؛ ویوهای owner بدون route (فایل تایپو `inance.py`)
4. هیچ تست خودکاری نیست — سناریوهای تست دستی در `/tmp/opencode/*.py` (موقت!) هستند
5. اکانت‌های آزمایشی تست (rev_*, race_*) پاک شده‌اند؛ داده‌های demo خرید (mr_karimi) در PG فعلی نیستند — PG از seed تمیز شروع شده

## ۹) سبک کار با این کارفرما
- فارسی جواب بده، خلاصه و جدول‌محور
- قبل از تغییرات بزرگ: plan mode → جدول مقایسه → سوالات شفاف‌سازی → بعد build
- هر تغییر: fix همزمان + re-test زنده با curl + کامیت تمیز با پیام توضیحی
