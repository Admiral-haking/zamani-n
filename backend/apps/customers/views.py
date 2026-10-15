from rest_framework import status
from rest_framework import viewsets

from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from rest_framework.filters import SearchFilter, OrderingFilter

from rest_framework.decorators import action

from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Q, OuterRef, Subquery


from .models import Customer, CustomerBackup

from .serializers import CustomerSerializer, CustomerBackupSerializer


from apps.audit.services import AuditService


from apps.common.permissions.permissions import (
    IsAdminOrSecretary,
    IsDistributor
)




class CustomerViewSet(viewsets.ModelViewSet):


    serializer_class = CustomerSerializer


    # تا مسیر بک‌آپ (customers/backup/) با شناسه مشتری تداخل نکند
    lookup_value_regex = r"(?!backup)[^/.]+"


    filter_backends = [

        DjangoFilterBackend,

        SearchFilter,

        OrderingFilter,

    ]



    filterset_fields = [

        "is_active",

    ]



    search_fields = [

        "customer_code",

        "company_name",

        "phone",

        "national_id",

        "user__username",

        "user__first_name",

        "user__last_name",

    ]



    ordering_fields = [

        "customer_code",

        "company_name",

        "created_at",

        "account_balance",

    ]



    ordering = [

        "-created_at"

    ]




    def get_queryset(self):


        user = self.request.user
        if not user.is_authenticated:
            return Customer.objects.none()


        from apps.orders.models import Order
        last_order = (
            Order.objects
            .filter(customer_id=OuterRef('id'))
            .exclude(status='CANCELLED')
            .order_by('-created_at')
            .values('created_at')[:1]
        )

        if user.is_superuser:
            queryset = Customer.objects.all()

        elif user.role in [
            "ADMIN",
            "SECRETARY"
        ]:
            queryset = (
                Customer.objects
                .select_related(
                    "user",
                    "distributor"
                )
                .all()
            )

        elif user.role == "DISTRIBUTOR":
            queryset = (
                Customer.objects
                .filter(
                    distributor__user=user
                )
                .select_related(
                    "user"
                )
            )

        elif user.role == "CUSTOMER":
            queryset = Customer.objects.filter(
                user=user
            )

        else:
            return Customer.objects.none()

        return queryset.annotate(
            last_purchase_at=Subquery(last_order)
        )
        return Customer.objects.none()




    def get_permissions(self):


        if self.action in [

            "create",

            "update",

            "partial_update",

            "destroy",

            "delete_forever",

        ]:


            return [

                IsAdminOrSecretary()

            ]



        return [

            IsAuthenticated()

        ]




    def perform_destroy(self, instance):
        """حذف پرونده مشتری (نرم): غیرفعال کردن مشتری و حساب کاربری"""
        user = instance.user
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        if user:
            user.is_active = False
            user.save(update_fields=["is_active"])

        AuditService.log(
            user=self.request.user,
            action="DELETE",
            model_name="Customer",
            object_id=instance.id,
            description=(
                f"Profile soft-deleted for Customer "
                f"{instance.company_name or instance.id} by {self.request.user.username}"
            )
        )

    @action(detail=True, methods=['post', 'put', 'patch'])
    def update_address(self, request, pk=None):
        """به‌روزرسانی آدرس توسط خود مشتری (فقط مالک)."""
        customer = self.get_object()

        is_owner = (
            request.user.is_authenticated
            and customer.user_id == request.user.id
        )
        is_staff = request.user.role in ['ADMIN', 'SECRETARY']

        if not is_staff and not is_owner:
            return Response(
                {'error': 'فقط صاحب حساب می‌تواند آدرس را تغییر دهد'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data or {}
        for field in ['address', 'city', 'state', 'postal_code', 'country']:
            if field in data and data[field] is not None:
                setattr(customer, field, str(data[field]).strip())

        customer.save()

        AuditService.log(
            user=request.user,
            action="UPDATE",
            model_name="Customer",
            object_id=customer.id,
            description=f"Address updated for Customer {customer.customer_code} by {request.user.username}"
        )

        return Response({
            'success': True,
            'message': 'آدرس با موفقیت به‌روزرسانی شد',
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'postal_code': customer.postal_code,
            'country': customer.country,
        })

    @action(detail=False, methods=["get"])
    def me(self, request):
        """پروفایل و price_list مشتریِ لاگین‌کرده (برای سایت مادر)."""

        customer = getattr(request.user, "customer_profile", None)
        if customer is None:
            return Response({
                "success": False,
                "message": "Customer profile not found",
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(customer).data)

    @action(detail=False, methods=["get"])
    def picks(self, request):
        """محصولاتی که مشتری در ۵ خریدِ آخر بیش از ۲ بار خریده است (برای سایت مادر)."""

        customer = getattr(request.user, "customer_profile", None)
        if customer is None:
            return Response({}, status=status.HTTP_200_OK)

        user_role = getattr(request.user, "role", "")
        if user_role != "CUSTOMER":
            return Response([], status=status.HTTP_200_OK)

        from collections import Counter
        from apps.orders.models import Order

        last_orders = list(
            Order.objects.filter(customer=customer)
            .order_by("-created_at")[:5]
            .prefetch_related("items__product")
        )

        order_count = Counter()
        total_qty = Counter()
        product_info = {}
        for order in last_orders:
            seen = set()
            for item in order.items.all():
                pid = item.product_id
                order_count[pid] += 1
                total_qty[pid] += item.quantity or 0
                if pid in seen:
                    continue
                seen.add(pid)
                if pid not in product_info:
                    product_info[pid] = {
                        "id": item.product_id,
                        "name": item.product.name,
                        "image": item.product.image,
                    }

        picks = []
        for pid, cnt in order_count.items():
            if cnt <= 2:
                continue
            info = product_info.get(pid) or {}
            picks.append({
                "id": pid,
                "name": info.get("name") or f"product-{pid}",
                "image": info.get("image") or None,
                "orders_count": cnt,
                "quantity": total_qty.get(pid, 0),
            })

        picks.sort(key=lambda x: (-x["orders_count"], -x["quantity"]))
        return Response(picks)

    def perform_create(self, serializer):


        user = self.request.user



        if user.role == "DISTRIBUTOR":


            customer = serializer.save(

                distributor=user.distributor_profile

            )


        else:


            customer = serializer.save()



        AuditService.log(

            user=user,

            action="CREATE",

            model_name="Customer",

            object_id=customer.id,

            description=f"Customer {customer.customer_code} created"

        )




    def perform_update(self, serializer):


        customer = serializer.save()



        AuditService.log(

            user=self.request.user,

            action="UPDATE",

            model_name="Customer",

            object_id=customer.id,

            description=f"Customer {customer.customer_code} updated"

        )




    def perform_destroy(self, instance):


        code = instance.customer_code

        pk = instance.id



        instance.soft_delete()



        AuditService.log(

            user=self.request.user,

            action="DELETE",

            model_name="Customer",

            object_id=pk,

            description=f"Customer {code} deleted"

        )




    def destroy(self, request, *args, **kwargs):


        instance = self.get_object()



        self.perform_destroy(

            instance

        )



        return Response(

            {

                "success": True,

                "message": "Customer deleted successfully."

            },

            status=status.HTTP_200_OK

        )

    @action(detail=True, methods=["post"])
    def delete_forever(self, request, pk=None):

        customer = self.get_object()

        code = customer.customer_code
        customer_id = customer.id

        # Ù‚Ø¨Ù„ Ø§Ø² Ø­Ø°ÙØŒ Ø¨Ú©â€ŒØ¢Ù¾ Ú©Ø§Ù…Ù„ (Ø§Ø·Ù„Ø§Ø¹Ø§Øª + Ú©Ù„ ØªØ§Ø±ÛŒØ®Ú†Ù‡) Ø°Ø®ÛŒØ±Ù‡ Ù…ÛŒâ€ŒØ´ÙˆØ¯
        from .services import archive_customer_backup
        archive_customer_backup(customer, actor=request.user)

        AuditService.log(
            user=request.user,
            action="DELETE",
            model_name="Customer",
            object_id=customer_id,
            description=f"Customer {code} permanently deleted"
        )

        # Ø­Ø°Ù Ø§Ú©Ø§Ù†Øª Ú©Ø§Ø±Ø¨Ø±ØŒ Ù…Ø´ØªØ±ÛŒ Ùˆ Ù‡Ù…Ù‡ Ø³ÙˆØ§Ø¨Ù‚ Ù…Ø±ØªØ¨Ø· (Ø³ÙØ§Ø±Ø´ØŒ Ù¾Ø±Ø¯Ø§Ø®ØªØŒ
        # Ø¨Ø§Ø²Ú¯Ø´ØªØŒ Ù‚ÛŒÙ…Øªâ€ŒÙ‡Ø§ØŒ ÛŒØ§Ø¯Ø¯Ø§Ø´Øªâ€ŒÙ‡Ø§ Ùˆ ØªÛŒÚ©Øªâ€ŒÙ‡Ø§) Ø¨Ù‡â€ŒØµÙˆØ±Øª Ø¢Ø¨Ø´Ø§Ø±ÛŒ.
        customer.user.delete()

        return Response(
            {
                "success": True,
                "message": "Customer removed permanently."
            },
            status=status.HTTP_200_OK
        )


class BackupPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomerBackupViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = CustomerBackupSerializer

    permission_classes = [IsAdminOrSecretary]

    pagination_class = BackupPagination

    def get_queryset(self):
        queryset = CustomerBackup.objects.all()
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search)
                | Q(full_name__icontains=search)
                | Q(shop_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(username__icontains=search)
                | Q(customer_code__icontains=search)
            )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.original_customer_id:
            current = Customer.objects.filter(
                id=instance.original_customer_id
            ).first()
            if current is not None:
                from .services import _fill_backup
                instance = _fill_backup(instance, current)

        serializer = self.get_serializer(instance)
        data = serializer.data
        data["snapshot"] = instance.snapshot or {}
        return Response(data)
