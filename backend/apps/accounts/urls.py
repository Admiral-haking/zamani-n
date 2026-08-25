from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views.auth_views import (
    LoginView,
    MeView,
    CreateDistributorView,
    CreateSecretaryView,
    CreateCustomerByStaffView,
)

urlpatterns = [
    # ثبت‌نام آزاد وجود ندارد؛ حساب‌ها فقط توسط ادمین کل / منشی ساخته می‌شوند
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),

    path("users/create-distributor/", CreateDistributorView.as_view(), name="create-distributor"),
    path("users/create-secretary/", CreateSecretaryView.as_view(), name="create-secretary"),
    path("users/create-customer/", CreateCustomerByStaffView.as_view(), name="create-customer"),
]
