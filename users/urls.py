from django.urls import path
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Force the empty home route to load the login page automatically
    path('', RedirectView.as_view(url='login/', permanent=False), name='root_redirect'),

    # Auth core
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_customer, name='register'),
    
    # Dashboards & routers
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/executive/', views.executive_dashboard, name='executive_dashboard'),
    path('dashboard/toggle-subscription/<int:user_id>/', views.toggle_subscription, name='toggle_subscription'),

    
    # Profile actions
    path('profile/edit/', views.edit_profile, name='edit_own_profile'),
    path('profile/edit/<int:user_id>/', views.edit_profile, name='edit_user_profile'),
    path('manage/create-user/', views.create_internal_user, name='create_internal_user'),

    # Payment
    path('checkout/', views.mock_checkout, name='mock_checkout'),

    path('manage/impersonate/<int:user_id>/', views.impersonate_user, name='impersonate_user'),
    path('manage/stop-impersonating/', views.stop_impersonating, name='stop_impersonating'),

    path('manage/audit-logs/', views.audit_log_view, name='audit_log_view'),





]
