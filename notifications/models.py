from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    # Extend default user with team association
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    def __str__(self) -> str:
        return self.get_username()


class Alert(models.Model):
    class Severity(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    class DeliveryType(models.TextChoices):
        IN_APP = 'in_app', 'In-App'
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'

    VISIBILITY_ORG = 'org'
    VISIBILITY_TEAM = 'team'
    VISIBILITY_USER = 'user'
    VISIBILITY_CHOICES = [
        (VISIBILITY_ORG, 'Organization'),
        (VISIBILITY_TEAM, 'Team'),
        (VISIBILITY_USER, 'User'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    delivery_type = models.CharField(max_length=20, choices=DeliveryType.choices, default=DeliveryType.IN_APP)

    # Visibility targeting
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=VISIBILITY_ORG)
    target_teams = models.ManyToManyField(Team, blank=True, related_name='alerts')
    target_users = models.ManyToManyField('User', blank=True, related_name='direct_alerts')

    start_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    reminder_frequency_minutes = models.PositiveIntegerField(default=120)
    reminders_enabled = models.BooleanField(default=True)

    archived = models.BooleanField(default=False)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_alerts')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title}"

    @property
    def is_active_now(self) -> bool:
        now = timezone.now()
        if self.archived:
            return False
        if self.start_at and now < self.start_at:
            return False
        if self.expires_at and now >= self.expires_at:
            return False
        return True


class NotificationDelivery(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='deliveries')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='deliveries')
    channel = models.CharField(max_length=20, choices=Alert.DeliveryType.choices, default=Alert.DeliveryType.IN_APP)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    message_snapshot = models.TextField(blank=True, default='')
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Delivery [{self.channel}] to {self.user} for {self.alert_id} at {self.sent_at:%Y-%m-%d %H:%M}"


class UserAlertPreference(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='user_preferences')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='alert_preferences')

    is_read = models.BooleanField(default=False)
    snoozed_on = models.DateField(null=True, blank=True)  # If set to today, skip reminders until next day
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('alert', 'user')

    def __str__(self) -> str:
        return f"Pref u={self.user_id} a={self.alert_id} read={self.is_read}"

    def is_snoozed_today(self) -> bool:
        if not self.snoozed_on:
            return False
        return self.snoozed_on == timezone.localdate()

# Create your models here.
