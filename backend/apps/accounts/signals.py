from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.distributors.models import Distributor


@receiver(post_save, sender=User)
def create_role_profiles(sender, instance, created, **kwargs):
    """
    پس از ثبت‌نام، پروفایل متناسب با نقش به صورت خودکار ساخته می‌شود تا
    دسترسی‌های customer_profile و distributor_profile همیشه معتبر باشند.
    """
    if not created:
        return

    if instance.role == User.Role.CUSTOMER:
        Customer.objects.get_or_create(
            user=instance,
            defaults={"phone": _unique_phone(instance)},
        )

    elif instance.role == User.Role.DISTRIBUTOR:
        Distributor.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": instance.get_full_name() or instance.username,
                "phone": _unique_phone(instance),
            },
        )


def _unique_phone(user):
    """Customer.phone و Distributor.phone یکتا هستند؛ در نبود یا تکرار شماره،
    یک شناسه جایگزین یکتا تولید می‌شود."""
    from uuid import uuid4

    if user.phone:
        phone_taken_customer = Customer.objects.filter(phone=user.phone).exists()
        phone_taken_distributor = Distributor.objects.filter(
            phone=user.phone
        ).exists()
        if not phone_taken_customer and not phone_taken_distributor:
            return user.phone
    # Distributor.phone is limited to 11 characters. Keep the generated
    # placeholder within that limit so automatic seed/user creation cannot
    # fail on the distributor profile.
    return f"T{uuid4().hex[:10]}"
