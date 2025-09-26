from django.contrib import admin
from .models import Team, User, Alert, NotificationDelivery, UserAlertPreference


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "team")
    list_filter = ("team",)
    search_fields = ("username", "email")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "severity", "delivery_type", "visibility", "start_at", "expires_at", "reminders_enabled", "archived")
    list_filter = ("severity", "delivery_type", "visibility", "reminders_enabled", "archived")
    search_fields = ("title", "message")
    filter_horizontal = ("target_teams", "target_users")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "alert", "user", "channel", "status", "sent_at")
    list_filter = ("channel", "status")
    search_fields = ("message_snapshot",)


@admin.register(UserAlertPreference)
class UserAlertPreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "alert", "user", "is_read", "snoozed_on", "last_reminded_at")
    list_filter = ("is_read",)
