"""
URL configuration for alerting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from notifications.views import AlertViewSet, MyAlertsViewSet, analytics_view
from notifications import web_views
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alerts')
router.register(r'my-alerts', MyAlertsViewSet, basename='my-alerts')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/analytics/', analytics_view),
    path('', web_views.home, name='home'),
    path('dashboard/', web_views.dashboard, name='dashboard'),
    path('teams/', web_views.manage_teams, name='manage_teams'),
    path('users/', web_views.manage_users, name='manage_users'),
    path('alerts/', web_views.manage_alerts, name='manage_alerts'),
    path('pref/<int:pref_id>/toggle-read/', web_views.toggle_read, name='toggle_read'),
    path('pref/<int:pref_id>/snooze-today/', web_views.snooze_today, name='snooze_today'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
