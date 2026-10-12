# backend/apps/tickets/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from datetime import datetime

from .models import Ticket, TicketMessage, TicketAttachment
from .serializers import TicketSerializer
from apps.audit.services import AuditService
from apps.common.permissions.permissions import IsAdminOrSecretary


class TicketViewSet(viewsets.ModelViewSet):
    """
    مدیریت کامل تیکت‌ها برای پنل منشی
    """
    
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'message', 'user__username', 'user__phone']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'guest_request':
            return [AllowAny()]
        if self.action in ['reply', 'close']:
            return [IsAuthenticated()]
        if self.action in ['assign', 'add_note', 'destroy']:
            return [IsAdminOrSecretary()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        # منشی و ادمین: همه تیکت‌ها با اطلاعات کاربر
        if user.role in ['ADMIN', 'SECRETARY']:
            return Ticket.objects.select_related('user').prefetch_related('messages__attachments').all()
        
        # توزیع‌کننده: تیکت‌های خودش
        if user.role == 'DISTRIBUTOR':
            return Ticket.objects.filter(user=user).select_related('user').prefetch_related('messages__attachments')
        
        # مشتری: تیکت‌های خودش
        if user.role == 'CUSTOMER':
            return Ticket.objects.filter(user=user).select_related('user').prefetch_related('messages__attachments')
        
        return Ticket.objects.none()

    def _create_initial_message(self, ticket, sender, sender_name):
        TicketMessage.objects.create(
            ticket=ticket,
            sender=sender,
            sender_name=sender_name,
            text=ticket.message or '',
        )

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        sender = TicketMessage.Sender.STAFF if self.request.user.role in ['ADMIN', 'SECRETARY'] else TicketMessage.Sender.CUSTOMER
        sender_name = self.request.user.get_full_name() or self.request.user.username
        self._create_initial_message(ticket, sender, sender_name)
        AuditService.log(
            user=self.request.user,
            action="CREATE",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Ticket #{ticket.id} created by {self.request.user.username}"
        )

    def perform_update(self, serializer):
        ticket = serializer.save()
        AuditService.log(
            user=self.request.user,
            action="UPDATE",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Ticket #{ticket.id} updated by {self.request.user.username}"
        )

    def perform_destroy(self, instance):
        ticket_id = instance.id
        instance.delete()
        AuditService.log(
            user=self.request.user,
            action="DELETE",
            model_name="Ticket",
            object_id=ticket_id,
            description=f"Ticket #{ticket_id} deleted by {self.request.user.username}"
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """پاسخ به تیکت: مشتری مالک پیام اضافه می‌کند، منشی/ادمین پاسخ می‌دهد.
        پشتیبانی از پیوست (تصویر/فایل) از طریق فیلد attachments (چند فایل)."""
        ticket = self.get_object()
        reply_message = str(request.data.get('reply_message') or '').strip()
        files = request.FILES.getlist('attachments')

        if not reply_message and not files:
            return Response(
                {'error': 'متن پاسخ یا فایل پیوست الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_owner = (
            request.user.is_authenticated
            and ticket.user_id == request.user.id
        )
        is_staff = request.user.role in ['ADMIN', 'SECRETARY']

        if not is_staff and not is_owner:
            return Response(
                {'error': 'فقط مالک تیکت یا پرسنل می‌توانند پاسخ دهند'},
                status=status.HTTP_403_FORBIDDEN
            )

        if is_staff:
            # پاسخ پرسنل در admin_reply می‌رود و تیکت ANSWERED می‌شود
            if reply_message:
                ticket.admin_reply = reply_message
            ticket.admin_replied_at = datetime.now()
            ticket.status = Ticket.Status.ANSWERED
            sender = TicketMessage.Sender.STAFF
        else:
            # پیام مشتری در customer_reply ثبت می‌شود و تیکت دوباره OPEN می‌شود (منتظر پرسنل)
            if reply_message:
                ticket.customer_reply = reply_message
            ticket.customer_replied_at = datetime.now()
            ticket.status = Ticket.Status.OPEN
            sender = TicketMessage.Sender.CUSTOMER

        sender_name = request.user.get_full_name() or request.user.username

        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=sender,
            sender_name=sender_name,
            text=reply_message,
        )

        for uploaded in files:
            TicketAttachment.objects.create(message=message, file=uploaded)

        ticket.save()

        ticket._prefetched_objects_cache = {}

        AuditService.log(
            user=request.user,
            action="REPLY",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Ticket #{ticket.id} replied by {request.user.username}"
        )

        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """بستن تیکت (مالک یا پرسنل)"""
        ticket = self.get_object()

        is_owner = (
            request.user.is_authenticated
            and ticket.user_id == request.user.id
        )
        is_staff = request.user.role in ['ADMIN', 'SECRETARY']

        if not is_staff and not is_owner:
            return Response(
                {'error': 'فقط مالک تیکت یا پرسنل می‌توانند تیکت را ببندند'},
                status=status.HTTP_403_FORBIDDEN
            )

        ticket.status = Ticket.Status.CLOSED
        ticket.save()
        
        AuditService.log(
            user=request.user,
            action="CLOSE",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Ticket #{ticket.id} closed by {request.user.username}"
        )
        
        return Response({'message': 'تیکت با موفقیت بسته شد'})

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """ارجاع تیکت به شخص دیگر"""
        ticket = self.get_object()
        assign_to = request.data.get('assign_to')
        
        if not assign_to:
            return Response(
                {'error': 'شناسه کاربر مقصد الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ذخیره اطلاعات ارجاع در admin_reply
        note = f"\n\n[ارجاع] تیکت به کاربر {assign_to} ارجاع داده شد توسط {request.user.username}"
        ticket.admin_reply = (ticket.admin_reply or '') + note
        ticket.save()
        
        AuditService.log(
            user=request.user,
            action="ASSIGN",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Ticket #{ticket.id} assigned to user {assign_to} by {request.user.username}"
        )
        
        return Response({'message': f'تیکت به کاربر {assign_to} ارجاع داده شد'})

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """افزودن یادداشت داخلی به تیکت"""
        ticket = self.get_object()
        note = request.data.get('note')
        
        if not note:
            return Response(
                {'error': 'متن یادداشت الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        note_text = f"\n\n[یادداشت داخلی] {note} - {request.user.username} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ticket.admin_reply = (ticket.admin_reply or '') + note_text
        ticket.save()
        
        AuditService.log(
            user=request.user,
            action="NOTE",
            model_name="Ticket",
            object_id=ticket.id,
            description=f"Note added to ticket #{ticket.id} by {request.user.username}"
        )
        
        return Response({'message': 'یادداشت با موفقیت ذخیره شد'})

    @action(detail=False, methods=['get'])
    def open_tickets(self, request):
        """لیست تیکت‌های باز (پاسخ داده نشده)"""
        tickets = self.get_queryset().filter(
            status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
        )
        serializer = self.get_serializer(tickets, many=True)
        return Response({
            'count': tickets.count(),
            'tickets': serializer.data
        })

    @action(detail=False, methods=['get'])
    def open_count(self, request):
        """تعداد تیکت‌های باز"""
        count = self.get_queryset().filter(
            status__in=[Ticket.Status.OPEN, Ticket.Status.ANSWERED]
        ).count()
        return Response({'open_tickets': count})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """آمار کامل تیکت‌ها"""
        queryset = self.get_queryset()
        
        open_tickets = queryset.filter(status=Ticket.Status.OPEN).count()
        answered = queryset.filter(status=Ticket.Status.ANSWERED).count()
        closed = queryset.filter(status=Ticket.Status.CLOSED).count()
        
        return Response({
            'open': open_tickets,
            'answered': answered,
            'closed': closed,
            'total': open_tickets + answered + closed,
        })
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        authentication_classes=[],
        url_path="guest-request",
    )
    def guest_request(self, request):
        """
        درخواست ایجاد حساب کاربری توسط کاربر ناشناس (بدون ثبت‌نام).
        تیکت به صف ادمین کل می‌رود و پس از تایید، مشتریِ زیرمجموعه
        ادمین کل ساخته می‌شود.
        """
        title = (request.data.get("title") or "").strip()
        message = (request.data.get("message") or "").strip()
        guest_name = (request.data.get("guest_name") or "").strip()
        guest_phone = (request.data.get("guest_phone") or "").strip()

        missing = [f for f, v in [
            ("guest_name", guest_name), ("guest_phone", guest_phone),
            ("message", message),
        ] if not v]
        if missing:
            return Response(
                {"error": f"فیلدهای الزامی: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket = Ticket.objects.create(
            user=None,
            title=title or "درخواست ایجاد حساب کاربری",
            message=message,
            category=Ticket.Category.ACCOUNT_REQUEST,
            guest_name=guest_name,
            guest_phone=guest_phone,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            sender=TicketMessage.Sender.GUEST,
            sender_name=guest_name,
            text=message,
        )
        return Response(
            {
                "id": ticket.id,
                "message": (
                    "درخواست شما ثبت شد؛ پس از بررسی توسط پشتیبانی "
                    "با شما تماس گرفته خواهد شد."
                ),
            },
            status=status.HTTP_201_CREATED,
        )
