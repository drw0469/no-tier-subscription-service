from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import CustomerRegistration, ProfileEditForm, StaffUserCreationForm
from .models import User, UserSubscription, SubscriptionAuditLog, PaymentLog

import time
import uuid

def register_customer(request):
    """Public registration endpoint strictly for customers."""
    if request.method == 'POST':
        form = CustomerRegistration(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard_router')
    else:
        form = CustomerRegistration()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard_router(request):
    """Routes users dynamically to their corrent workspace on login."""
    if request.user.is_admin_member:
        return redirect('admin_dashboard')
    elif request.user.is_staff_member:
        return redirect('staff_dashboard')
    elif request.user.is_customer:
        return redirect('customer_dashboard')
    return PermissionDenied


@login_required
def customer_dashboard(request):
    if not request.user.is_customer:
        raise PermissionDenied

    subscription = getattr(request.user, 'subscription', None)
    payments = []

    if subscription:
        # Pull past logs sorted by latest date
        payments = subscription.payments.all()
    
    return render(request, 'dashboards/customer.html', {
        'subscription': subscription,
        'payments': payments
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_admin_member:
        raise PermissionDenied
    
    # 1. Fetch search query from URL parameter (?search=xyz)
    search_query = request.GET.get('search', '').strip()
    
    # 2. Base Query logic
    customer_query = User.objects.filter(is_customer=True)
    
    # 3. Apply Multi-Field Database Filter if search query exists
    if search_query:
        customer_query = customer_query.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Order records so pagination remains deterministic
    all_customers = customer_query.order_by('username')
    staff = User.objects.filter(is_staff_member=True)

    # 4. Customer Pagination Chunking
    customer_paginator = Paginator(all_customers, 10) 
    customer_page_num = request.GET.get('page')
    customers_page = customer_paginator.get_page(customer_page_num)


    return render(request, 'dashboards/admin.html', {
        'customers': customers_page, 
        'staff': staff,
        'search_query': search_query  # <-- Pass search string back to keep input field filled
    })


@login_required
def staff_dashboard(request):
    if not (request.user.is_staff_member or request.user.is_admin_member):
        raise PermissionDenied
        
    search_query = request.GET.get('search', '').strip()
    customer_query = User.objects.filter(is_customer=True)
    
    if search_query:
        customer_query = customer_query.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        
    all_customers = customer_query.order_by('username')

    customer_paginator = Paginator(all_customers, 10)
    customer_page_num = request.GET.get('page')
    customers_page = customer_paginator.get_page(customer_page_num)

    return render(request, 'dashboards/staff.html', {
        'customers': customers_page,
        'search_query': search_query
    })


@login_required
def edit_profile(request, user_id=None):
    """Dynamic edit view parsing authorization hierarchies."""
    if user_id is None:
        target_user = request.user
    else:
        target_user = get_object_or_404(User, id=user_id)

    if request.user != target_user:
        if request.user.is_customer:
            raise PermissionDenied
        if request.user.is_staff_member and not target_user.is_customer:
            raise PermissionDenied

    if request.method == 'POST':
        # SECURITY OVERRIDE: Block database writes if the session is an impersonator
        if request.session.get('is_impersonating'):
            messages.error(request, "Security Notice: Profile updates are locked down while in 'Login-As' mode.")
            return redirect('customer_dashboard')
            
        form = ProfileEditForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            return redirect('dashboard_router')
        else:
            print("Form errors detected:", form.errors)
    else:
        form = ProfileEditForm(instance=target_user)

    return render(request, 'edit_profile.html', {'form': form, 'target_user': target_user})


    return render(request, 'edit_profile.html', {'form': form, 'target_user': target_user})

@login_required
def create_internal_user(request):
    """Restricted explicitly to Admins for creating staff/admins."""
    if not request.user.is_admin_member:
        raise PermissionDenied
    if request.method == 'POST':
        form = StaffUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = StaffUserCreationForm()
    return render(request, 'admin/create_staff.html', {'form': form})


@login_required
def toggle_subscription(request, user_id):
    """Allows Staff and Admins to safely toggle subscriptons with an audit trail note."""
    if not (request.user.is_staff_member or request.user.is_admin_member):
        raise PermissionDenied

    if request.method == "POST":
        target_user = get_object_or_404(User, id=user_id)
        action_type = str(request.POST.get('action_type', '')).strip().lower()  # 'activate' or 'deactivate'
        reason_note = request.POST.get('reason_notes', '').strip()

        if not reason_note:
            messages.error(request, "You must provide a reason note for this subscription modification.")
            return redirect('dashboard_router')

        # Get or create the underlying subscriptions record instance
        subscription, created = UserSubscription.objects.get_or_create(
            user=target_user,
            defaults={'is_active': False}
        )

        # Force structural tracking evaluation loops
        if action_type == 'activate':
            subscription.is_active = True
            subscription.save()

            # Generate unalterable audit row entry
            SubscriptionAuditLog.objects.create(
                customer=target_user,
                performed_by=request.user,
                action='activated',
                notes=reason_note
            )
            messages.success(request, f"Successfully activated subscription access for {target_user.username}")

        elif action_type == 'deactivate':
            subscription.is_active = False
            subscription.save()
            # Generate unalterable audit row entry
            SubscriptionAuditLog.objects.create(
                customer=target_user,
                performed_by=request.user,
                action='deactivated',
                notes=reason_note
            )
            messages.success(request, f"Successfully deactivated subscription access for {target_user.username}")

    return redirect('dashboard_router')



@login_required
def audit_log_view(request):
    """Dedicated, searchable audit trail log directory for Staff and Admins."""
    if not (request.user.is_staff_member or request.user.is_admin_member):
        raise PermissionDenied

    # 1. Capture search query specifically filtering target customers
    search_query = request.GET.get('search', '').strip()
    audit_query = SubscriptionAuditLog.objects.all().select_related('customer', 'performed_by')

    if search_query:
        audit_query = audit_query.filter(
            Q(customer__username__icontains=search_query) |
            Q(performed_by__username__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # 2. Order by latest logs first
    ordered_logs = audit_query.order_by('-created_at')

    # 3. Simple standalone pagination (15 records per page)
    paginator = Paginator(ordered_logs, 15)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)

    return render(request, 'admin/audit_logs.html', {
        'audit_logs': logs_page,
        'search_query': search_query
    })




@login_required
def mock_checkout(request):
    """Simulates an internal sandbox payment checkout screen for development."""
    subscription, created = UserSubscription.objects.get_or_create(
        user=request.user,
        defaults={'is_active': False}
    )
    
    if subscription.has_valid_access:
        return redirect('dashboard_router')

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').replace(' ', '')
        
        if len(card_number) < 12:
            messages.error(request, "Simulated Transaction Failed: Invalid credit card length.")
            return render(request, 'payments/mock_checkout.html')

        # 1. Update the Subscription to Active
        subscription.is_active = True
        subscription.save()

        # 2. ADD THIS: Generate a real history log entry for this cash exchange
        PaymentLog.objects.create(
            subscription=subscription,
            amount=99.99,
            transaction_id=f"TXN-{uuid.uuid4().hex[:8].upper()}",  # Generates e.g., TXN-A1B2C3D4
            status='completed'
        )

        # 3. Log the action into your unalterable audit log
        SubscriptionAuditLog.objects.create(
            customer=request.user,
            performed_by=None,
            action='activated',
            notes="Internal Sandbox Checkout: Automated user checkout completed."
        )

        messages.success(request, "Success! Your mock payment cleared and your annual account is now active! 🎉")
        return redirect('dashboard_router')

    return render(request, 'payments/mock_checkout.html')


@login_required
def impersonate_user(request, user_id):
    """Logs a staff/admin into a customer account while preserving their original identity."""
    if not (request.user.is_staff_member or request.user.is_admin_member):
        raise PermissionDenied

    target_user = get_object_or_404(User, id=user_id, is_customer=True)
    
    # 1. Capture the operator ID values into temporary local memory variables first
    original_uid = request.user.id

    # 2. TRIGGER AUTHENTICATION FIRST: This cycle handles flushing the session safely
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
    
    # 3. MOVED BELOW LOGIN: Assign your tracking states to the newly generated session
    request.session['original_user_id'] = original_uid
    request.session['is_impersonating'] = True
    
    messages.info(request, f"Now impersonating {target_user.username}. Actions are read-only.")
    return redirect('customer_dashboard')



@login_required
def stop_impersonating(request):
    """Reverts the session back to the original staff/admin user account."""
    original_user_id = request.session.get('original_user_id')
    
    if not original_user_id:
        return redirect('dashboard_router')

    original_user = get_object_or_404(User, id=original_user_id)
    
    # Clear the tracking states from the active session cache
    if 'original_user_id' in request.session:
        del request.session['original_user_id']
    if 'is_impersonating' in request.session:
        del request.session['is_impersonating']

    # Log back into the original staff/admin account profile
    login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
    
    messages.success(request, f"Impersonation ended. Returned to workspace: {original_user.username}.")
    return redirect('dashboard_router')





