from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout as auth_logout
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AlertForm, TeamForm, AdminUserForm
from .models import Alert, Team, User, UserAlertPreference
from .services import deliver_alert


def home(request):
    return render(request, "home.html")


def logout_to_home(request):
    auth_logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    user = request.user
    now = timezone.now()
    # visible = Alert.objects.filter(archived=False).filter(
    #     (Alert.objects.none() | Alert.objects.all())
    # )
    # # Same logic as API, expanded for readability
    # visible = Alert.objects.filter(archived=False)
    # visible = visible.filter(start_at__lte=now).filter(
    #     (timezone.now() is not None)
    # )
    visible = Alert.objects.filter(archived=False, start_at__lte=now)

    # Build visibility query
    from django.db.models import Q

    q = Q(visibility=Alert.VISIBILITY_ORG)
    if user.team_id:
        q |= Q(visibility=Alert.VISIBILITY_TEAM, target_teams__in=[user.team_id])
    q |= Q(visibility=Alert.VISIBILITY_USER, target_users=user)
    visible = visible.filter(q).distinct()

    prefs = []
    for alert in visible:
        pref, _ = UserAlertPreference.objects.get_or_create(alert=alert, user=user)
        prefs.append(pref)
    return render(
        request,
        "dashboard.html",
        {
            "preferences": prefs,
        },
    )


def staff_required(view):
    return user_passes_test(lambda u: u.is_staff, login_url="/login/")(view)


@login_required
@staff_required
def manage_teams(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Team saved")
            return redirect("manage_teams")
    else:
        form = TeamForm()
    teams = Team.objects.all()
    return render(request, "manage_teams.html", {"form": form, "teams": teams})


@login_required
@staff_required
def manage_users(request):
    if request.method == "POST":
        form = AdminUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if not user.has_usable_password():
                user.set_password("password")
                user.save()
            messages.success(request, "User created (default password: password)")
            return redirect("manage_users")
    else:
        form = AdminUserForm()
    users = User.objects.select_related("team").all()
    return render(request, "manage_users.html", {"form": form, "users": users})


@login_required
@staff_required
def manage_alerts(request, alert_id: int | None = None):
    alert_instance = Alert.objects.filter(id=alert_id).first() if alert_id else None
    if request.method == "POST":
        form = AlertForm(request.POST, instance=alert_instance)
        if form.is_valid():
            alert = form.save(commit=False)
            if alert_instance is None:
                alert.created_by = request.user
            alert.save()
            form.save_m2m()
            messages.success(request, "Alert saved")
            if "deliver_now" in request.POST:
                delivered = deliver_alert(alert)
                messages.info(request, f"Delivered to {delivered} users")
            return redirect("manage_alerts")
    else:
        form = AlertForm(instance=alert_instance)
        if alert_instance:
            messages.info(request, "Editing existing alert")
    alerts = Alert.objects.all().order_by("-created_at")
    return render(request, "manage_alerts.html", {"form": form, "alerts": alerts, "editing": alert_instance})


@login_required
def toggle_read(request, pref_id: int):
    pref = get_object_or_404(UserAlertPreference, id=pref_id, user=request.user)
    pref.is_read = not pref.is_read
    pref.save(update_fields=["is_read", "updated_at"])
    messages.success(request, f"Marked as {'read' if pref.is_read else 'unread'}")
    return redirect("dashboard")


@login_required
def snooze_today(request, pref_id: int):
    pref = get_object_or_404(UserAlertPreference, id=pref_id, user=request.user)
    pref.snoozed_on = timezone.localdate()
    pref.save(update_fields=["snoozed_on", "updated_at"])
    messages.info(request, "Snoozed for today")
    return redirect("dashboard")


