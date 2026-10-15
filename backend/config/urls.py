from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .health import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health, name='health'),
]

# ========================================
# API های پروژه
# ========================================

api_patterns = [
    path('accounts/', include('apps.accounts.urls')),
    path('products/', include('apps.products.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('pricing/', include('apps.pricing.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('payments/', include('apps.payments.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reminders/', include('apps.reminders.urls')),
    path('sms/', include('apps.sms.urls')),
    path('reports/', include('apps.reports.urls')),
    path('customers/', include('apps.customers.urls')),
    path('distributors/', include('apps.distributors.urls')),
    path('audit/', include('apps.audit.urls')),
    path('returns/', include('apps.returns.urls')),
    path('finance/', include('apps.finance.urls')),
]

urlpatterns += [
    path('api/', include(api_patterns)),
]

# Swagger
urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/owner/', include('apps.owner.urls')),
]

# ========================================
# سرو فایل‌های آپلودشده (در حالت DEBUG)
# ========================================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
