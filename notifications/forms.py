from django import forms

from .models import Alert, Team, User


class BaseStyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if isinstance(widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.DateTimeInput, forms.DateInput, forms.TimeInput, forms.Textarea)):
                widget.attrs["class"] = (css + " form-control").strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = (css + " form-select").strip()
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = (css + " form-check-input").strip()


class TeamForm(BaseStyledModelForm):
    class Meta:
        model = Team
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Team name (e.g., Engineering)"}),
        }


class AdminUserForm(BaseStyledModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "team", "is_staff", "is_superuser"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "username"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
        }


class AlertForm(BaseStyledModelForm):
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
            "title": forms.TextInput(attrs={"placeholder": "Alert title"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the alert"}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


