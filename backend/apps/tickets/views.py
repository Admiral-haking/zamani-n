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
        if self.action in ['guest_request', 'contact_messages_submit', 'support_chats_send', 'support_chats_mine']:
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
        methods=['get'],
        permission_classes=[IsAdminOrSecretary],
        url_path='support-chats/unread_count',
    )
    def support_chats_unread_count(self, request):
        return Response({'unread': Ticket.objects.filter(user__isnull=True, status=Ticket.Status.OPEN).count()})

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminOrSecretary],
        url_path='support-chats',
    )
    def support_chats(self, request):
        tickets = Ticket.objects.filter(user__isnull=True).prefetch_related('messages__attachments').order_by('-updated_at')
        data = []
        for ticket in tickets:
            messages = list(ticket.messages.all())
            last = messages[-1] if messages else None
            data.append({
                'id': ticket.id,
                'status': ticket.status,
                'display_name': ticket.guest_name or 'مهمان',
                'guest_phone': ticket.guest_phone,
                'subject_display': ticket.title,
                'last_message': last.text if last else ticket.message,
                'last_message_at': last.created_at if last else ticket.created_at,
                'created_at': ticket.created_at,
                'unread_count': 1 if ticket.status == Ticket.Status.OPEN else 0,
                'messages': [self._public_message(message) for message in messages],
            })
        return Response(data)
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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminOrSecretary],
        url_path='contact-messages',
    )
    def contact_messages(self, request):
        """Compatibility feed for the secretary's public contact inbox."""
        queryset = Ticket.objects.filter(user__isnull=True).prefetch_related('messages').order_by('-created_at')
        data = []
        subject_by_category = {
            Ticket.Category.ORDER: 'order', Ticket.Category.TECHNICAL: 'support',
            Ticket.Category.COMPLAINT: 'complaint', Ticket.Category.SUGGESTION: 'suggestion',
        }
        for ticket in queryset:
            data.append({
                'id': ticket.id,
                'full_name': ticket.guest_name or 'مهمان',
                'phone': ticket.guest_phone,
                'email': ticket.guest_email,
                'subject': subject_by_category.get(ticket.category, 'other'),
                'message': ticket.message,
                'status': 'answered' if ticket.status == Ticket.Status.ANSWERED else 'new',
                'is_read': ticket.status != Ticket.Status.OPEN,
                'created_at': ticket.created_at,
            })
        return Response(data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminOrSecretary],
        url_path='mark-read',
    )
    def contact_message_mark_read(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = Ticket.Status.ANSWERED
        ticket.save(update_fields=['status', 'updated_at'])
        return Response({'id': ticket.id, 'status': 'answered'})

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny],
        authentication_classes=[],
        url_path='contact-messages/submit',
    )
    def contact_messages_submit(self, request):
        """Public contact form; persist it as a guest ticket for staff."""
        name = (request.data.get('full_name') or '').strip()
        message = (request.data.get('message') or '').strip()
        phone = (request.data.get('phone') or '').strip()
        subject = (request.data.get('subject') or 'other').strip()
        email = (request.data.get('email') or '').strip()
        if not name or not message:
            return Response({'detail': 'نام و متن پیام الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        category = {
            'order': Ticket.Category.ORDER,
            'support': Ticket.Category.TECHNICAL,
            'complaint': Ticket.Category.COMPLAINT,
            'suggestion': Ticket.Category.SUGGESTION,
        }.get(subject, Ticket.Category.GENERAL)
        ticket = Ticket.objects.create(
            user=None, guest_name=name, guest_phone=phone, guest_email=email,
            title=f'پیام تماس: {subject}', message=message, category=category,
        )
        self._create_initial_message(ticket, TicketMessage.Sender.GUEST, name)
        return Response({'id': ticket.id, 'message': 'پیام شما ثبت شد.'}, status=status.HTTP_201_CREATED)

    def _public_message(self, message):
        return {
            'id': message.id,
            'sender': message.sender,
            'sender_name': message.sender_name,
            'text': message.text,
            'created_at': message.created_at,
            'attachments': [
                {'id': item.id, 'name': item.file.name.rsplit('/', 1)[-1], 'url': item.file.url}
                for item in message.attachments.all()
            ],
        }

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny],
        authentication_classes=[],
        url_path='support-chats/mine',
    )
    def support_chats_mine(self, request):
        key = (request.query_params.get('guest_key') or '').strip()
        if not key:
            return Response({'chat': None})
        ticket = Ticket.objects.filter(guest_key=key).prefetch_related('messages').first()
        if not ticket:
            return Response({'chat': None})
        return Response({'chat': {'id': ticket.id, 'status': ticket.status, 'messages': [self._public_message(m) for m in ticket.messages.all()]}})

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[AllowAny],
        authentication_classes=[],
        url_path='support-chats/send',
    )
    def support_chats_send(self, request):
        key = (request.data.get('guest_key') or '').strip()
        text = (request.data.get('text') or '').strip()
        name = (request.data.get('guest_name') or '').strip()
        phone = (request.data.get('guest_phone') or '').strip()
        if not key or not text:
            return Response({'detail': 'شناسه مهمان و متن پیام الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        ticket = Ticket.objects.filter(guest_key=key).first()
        if not ticket:
            ticket = Ticket.objects.create(
                user=None, guest_key=key, guest_name=name, guest_phone=phone,
                title='گفتگوی پشتیبانی آنلاین', message=text,
                category=Ticket.Category.GENERAL,
            )
            sender = TicketMessage.Sender.GUEST
        else:
            sender = TicketMessage.Sender.GUEST
        msg = TicketMessage.objects.create(ticket=ticket, sender=sender, sender_name=name or ticket.guest_name or 'مهمان', text=text)
        for uploaded in request.FILES.getlist('files'):
            TicketAttachment.objects.create(message=msg, file=uploaded)
        return Response({'chat_id': ticket.id, 'message': self._public_message(msg)}, status=status.HTTP_201_CREATED)
