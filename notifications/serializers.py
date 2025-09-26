from typing import Any

from django.utils import timezone
from rest_framework import serializers

from .models import Alert, Team, User, UserAlertPreference


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "team"]


class AlertSerializer(serializers.ModelSerializer):
    target_team_ids = serializers.PrimaryKeyRelatedField(
        source="target_teams",
        many=True,
        queryset=Team.objects.all(),
        required=False,
        write_only=True,
    )
    target_user_ids = serializers.PrimaryKeyRelatedField(
        source="target_users",
        many=True,
        queryset=User.objects.all(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Alert
        fields = [
            "id",
            "title",
            "message",
            "severity",
            "delivery_type",
            "visibility",
            "target_team_ids",
            "target_user_ids",
            "start_at",
            "expires_at",
            "reminder_frequency_minutes",
            "reminders_enabled",
            "archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data: dict[str, Any]) -> Alert:
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault("created_by", request.user)
        alert = super().create(validated_data)
        return alert


class UserAlertPreferenceSerializer(serializers.ModelSerializer):
    alert = AlertSerializer(read_only=True)

    class Meta:
        model = UserAlertPreference
        fields = [
            "id",
            "alert",
            "is_read",
            "snoozed_on",
            "last_reminded_at",
            "first_seen_at",
            "updated_at",
        ]
        read_only_fields = ["last_reminded_at", "first_seen_at", "updated_at"]


class MarkReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()


class SnoozeSerializer(serializers.Serializer):
    snooze_for_today = serializers.BooleanField(default=True)

    def save(self, preference: UserAlertPreference) -> UserAlertPreference:
        if self.validated_data.get("snooze_for_today"):
            preference.snoozed_on = timezone.localdate()
        else:
            preference.snoozed_on = None
        preference.save(update_fields=["snoozed_on", "updated_at"])
        return preference


