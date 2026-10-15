import re

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions.distributor_access import IsDistributorOrAdminSecretary
from apps.customers.models import Customer
from .models import SmsMessage
from .serializers import SmsMessageSerializer


FA_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def normalize_phone(raw):
    """یکنواخت‌سازی شماره موبایل فارسی/عربی به انگلیسی"""
    if raw is None:
        return ''
    s = str(raw).translate(FA_DIGITS)
    s = re.sub(r'[\s\-()]', '', s)
    if s.startswith('+98'):
        s = '0' + s[3:]
    elif s.startswith('98') and len(s) == 12:
        s = '0' + s[2:]
    return s


def _distributor_profile(user):
    return getattr(user, 'distributor_profile', None)


class SmsViewSet(viewsets.ModelViewSet):
    """ثبت و تاریخچه پیامک‌ها — پخش‌کننده فقط مشتریان خودش"""

    serializer_class = SmsMessageSerializer
    permission_classes = [IsDistributorOrAdminSecretary]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = SmsMessage.objects.select_related('customer', 'customer__user', 'sender')
        if not user.is_authenticated:
            return qs.none()
        if user.role in ['ADMIN', 'SECRETARY']:
            return qs.all()
        if user.role == 'DISTRIBUTOR':
            profile = _distributor_profile(user)
            if profile is None:
                return qs.none()
            return qs.filter(customer__distributor=profile)
        return qs.none()

    @action(detail=False, methods=['post'])
    def send(self, request):
        """ثبت پیامک تکی؛ یافتن مشتری در محدوده دسترسی و ذخیره در تاریخچه"""
        phone = normalize_phone(request.data.get('phone'))
        subject = (request.data.get('subject') or '').strip()
        body = (request.data.get('body') or '').strip()

        if not re.fullmatch(r'09\d{9}', phone or ''):
            return Response(
                {'error': 'شماره موبایل معتبر وارد کنید (مثل 09123456789).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not body:
            return Response(
                {'error': 'متن پیامک را وارد کنید.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        customer = None
        cust_qs = Customer.objects.filter(phone=phone)
        if user.role in ['ADMIN', 'SECRETARY']:
            customer = cust_qs.first()
        elif user.role == 'DISTRIBUTOR':
            profile = _distributor_profile(user)
            if profile is not None:
                customer = cust_qs.filter(distributor=profile).first()

        # درگاه پیامک هنوز متصل نیست؛ پیام ثبت و در تاریخچه نگه‌داری می‌شود
        msg = SmsMessage.objects.create(
            customer=customer,
            sender=user,
            phone=phone,
            subject=subject,
            body=body,
            status=SmsMessage.Status.LOGGED,
        )
        return Response(
            {
                'message': 'پیامک با موفقیت ثبت شد.',
                'data': SmsMessageSerializer(msg).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def send_bulk(self, request):
        """ثبت پیامک گروهی برای مشتریان محدوده دسترسی (فیلتر گروه)"""
        group = (request.data.get('group') or 'all').strip()
        subject = (request.data.get('subject') or '').strip()
        body = (request.data.get('body') or '').strip()

        if not body:
            return Response(
                {'error': 'متن پیامک را وارد کنید.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        cust_qs = Customer.objects.all()
        if user.role in ['ADMIN', 'SECRETARY']:
            pass
        elif user.role == 'DISTRIBUTOR':
            profile = _distributor_profile(user)
            if profile is None:
                return Response({'error': 'پروفایل پخش‌کننده یافت نشد.'}, status=status.HTTP_403_FORBIDDEN)
            cust_qs = cust_qs.filter(distributor=profile)
        else:
            return Response({'error': 'دسترسی ندارید.'}, status=status.HTTP_403_FORBIDDEN)

        if group == 'active':
            cust_qs = cust_qs.filter(is_active=True)
        elif group == 'inactive':
            cust_qs = cust_qs.filter(is_active=False)
        else:
            cust_qs = cust_qs.filter(is_active=True)

        created = 0
        for c in cust_qs.iterator():
            phone = normalize_phone(c.phone)
            if not re.fullmatch(r'09\d{9}', phone or ''):
                continue
            SmsMessage.objects.create(
                customer=c, sender=user, phone=phone,
                subject=subject, body=body,
                status=SmsMessage.Status.LOGGED,
            )
            created += 1

        return Response(
            {'message': f'پیامک برای {created} مخاطب ثبت شد.', 'count': created},
            status=status.HTTP_201_CREATED,
        )
