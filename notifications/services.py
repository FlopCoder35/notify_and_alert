from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable, Protocol

from django.db import transaction
from django.utils import timezone

from .models import Alert, NotificationDelivery, User, UserAlertPreference


class NotificationChannel(Protocol):
    def send(self, user: User, alert: Alert) -> bool: ...


@dataclass
class InAppChannel:
    def send(self, user: User, alert: Alert) -> bool:
        NotificationDelivery.objects.create(
            alert=alert,
            user=user,
            channel=Alert.DeliveryType.IN_APP,
            status=NotificationDelivery.Status.SENT,
            message_snapshot=alert.message,
        )
        return True


CHANNEL_REGISTRY: dict[str, NotificationChannel] = {
    Alert.DeliveryType.IN_APP: InAppChannel(),
}


def get_channel(channel_key: str) -> NotificationChannel:
    return CHANNEL_REGISTRY[channel_key]


def iter_visible_users(alert: Alert) -> Iterable[User]:
    if alert.visibility == Alert.VISIBILITY_ORG:
        return User.objects.all()
    if alert.visibility == Alert.VISIBILITY_TEAM:
        return User.objects.filter(team__in=alert.target_teams.all())
    if alert.visibility == Alert.VISIBILITY_USER:
        return alert.target_users.all()
    return User.objects.none()


@transaction.atomic
def deliver_alert(alert: Alert) -> int:
    if not alert.is_active_now:
        return 0
    channel = get_channel(alert.delivery_type)
    sent_count = 0
    for user in iter_visible_users(alert):
        pref, _ = UserAlertPreference.objects.get_or_create(alert=alert, user=user)
        if pref.is_snoozed_today():
            continue
        channel.send(user, alert)
        pref.last_reminded_at = timezone.now()
        pref.save(update_fields=["last_reminded_at", "updated_at"])
        sent_count += 1
    return sent_count


def should_remind(pref: UserAlertPreference) -> bool:
    if pref.alert.archived or not pref.alert.reminders_enabled:
        return False
    if not pref.alert.is_active_now:
        return False
    if pref.is_read:
        return False
    if pref.is_snoozed_today():
        return False
    if pref.last_reminded_at is None:
        return True
    return timezone.now() - pref.last_reminded_at >= timedelta(minutes=pref.alert.reminder_frequency_minutes)


def trigger_reminders() -> int:
    to_notify: list[UserAlertPreference] = []
    qs = UserAlertPreference.objects.select_related("alert").all()
    for pref in qs:
        if should_remind(pref):
            to_notify.append(pref)
    count = 0
    for pref in to_notify:
        channel = get_channel(pref.alert.delivery_type)
        channel.send(pref.user, pref.alert)
        pref.last_reminded_at = timezone.now()
        pref.save(update_fields=["last_reminded_at", "updated_at"])
        count += 1
    return count


