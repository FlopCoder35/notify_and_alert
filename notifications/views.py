from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import Alert, NotificationDelivery, UserAlertPreference
from .serializers import (
    AlertSerializer,
    AlertAdminListSerializer,
    MarkReadSerializer,
    SnoozeSerializer,
    UserAlertPreferenceSerializer,
)
from .services import deliver_alert


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by("-created_at")
    serializer_class = AlertSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["severity", "archived", "reminders_enabled", "visibility"]

    def get_serializer_class(self):
        if self.action == 'list' and self.request and self.request.user and self.request.user.is_staff:
            return AlertAdminListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param == 'active':
            qs = [a for a in qs if a.is_active_now]
        elif status_param == 'expired':
            qs = [a for a in qs if not a.is_active_now]
        # annotate metrics for admin list
        from django.db.models import Count, Q
        from django.utils import timezone as tz
        today = tz.localdate()
        return (
            Alert.objects.filter(id__in=[a.id for a in qs])
            .annotate(
                num_preferences=Count('user_preferences', distinct=True),
                num_read=Count('user_preferences', filter=Q(user_preferences__is_read=True), distinct=True),
                num_unread=Count('user_preferences', filter=Q(user_preferences__is_read=False), distinct=True),
                num_snoozed_today=Count('user_preferences', filter=Q(user_preferences__snoozed_on=today), distinct=True),
            )
            .order_by('-created_at')
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def deliver_now(self, request, pk=None):
        alert = self.get_object()
        count = deliver_alert(alert)
        return Response({"delivered": count})


class MyAlertsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserAlertPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure preferences exist for visible, active alerts
        user = self.request.user
        now = timezone.now()
        visible = Alert.objects.filter(archived=False).filter(
            Q(visibility=Alert.VISIBILITY_ORG)
            | Q(visibility=Alert.VISIBILITY_TEAM, target_teams__in=[user.team_id] if user.team_id else [])
            | Q(visibility=Alert.VISIBILITY_USER, target_users=user)
        ).distinct()
        visible = visible.filter(start_at__lte=now).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        # Create missing prefs
        for alert in visible:
            UserAlertPreference.objects.get_or_create(alert=alert, user=user)
        return UserAlertPreference.objects.filter(user=user).select_related("alert")

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        pref = self.get_object()
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pref.is_read = serializer.validated_data["is_read"]
        pref.save(update_fields=["is_read", "updated_at"])
        return Response({"is_read": pref.is_read})

    @action(detail=True, methods=["post"], url_path="snooze")
    def snooze(self, request, pk=None):
        pref = self.get_object()
        serializer = SnoozeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(preference=pref)
        return Response({"snoozed_on": pref.snoozed_on})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def analytics_view(request):
    total_alerts = Alert.objects.count()
    deliveries = NotificationDelivery.objects.count()
    read_count = UserAlertPreference.objects.filter(is_read=True).count()
    snoozed_today = UserAlertPreference.objects.filter(snoozed_on=timezone.localdate()).count()
    severity_breakdown = (
        Alert.objects.values("severity").annotate(count=Count("id")).order_by()
    )
    return Response(
        {
            "total_alerts": total_alerts,
            "deliveries": deliveries,
            "read": read_count,
            "snoozed_today": snoozed_today,
            "severity_breakdown": list(severity_breakdown),
        }
    )


# Create your views here.
