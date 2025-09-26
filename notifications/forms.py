from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Alert, Team, User


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name"]


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "team", "is_staff", "is_superuser"]


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = [
            "title",
            "message",
            "severity",
            "delivery_type",
            "visibility",
            "target_teams",
            "target_users",
            "start_at",
            "expires_at",
            "reminder_frequency_minutes",
            "reminders_enabled",
            "archived",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


