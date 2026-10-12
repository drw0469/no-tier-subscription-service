from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Custom User Model with specific roles."""
    is_customer = models.BooleanField(default=False)
    is_staff_member = models.BooleanField(default=False)
    is_admin_member = models.BooleanField(default=False)
    is_executive_member = models.BooleanField(default=False)

    # Profile information
    bio = models.TextField(blank=True, max_length=500)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.username} ({self.email})"


class UserSubscription(models.Model):
    """Tracks the single annual subscription status for a customer."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    # For payment tracking
    customer_gateway_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_gateway_id = models.CharField(max_length=255, blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=365)
        super().save(*args, **kwargs)

    @property
    def has_valid_access(self):
        return self.is_active and timezone.now() < self.end_date

    def __str__(self):
        return f"{self.user.username}'s Annual Subscrition"

class SubscriptionAuditLog(models.Model):
    """Tracks manual subscription modifications by staff or admins."""
    ACTION_CHOICES = [
        ('activated', 'Activated Access'),
        ('deactivated', 'Deactivated'),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_audit_logs'
    )

    # The staff member or admin who clicked the button
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_logged'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, help_text="Reason for modification")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor = self.performed_by.username if self.performed_by else "System"
        return f"{actor} {self.action} for {self.customer.username} on {self.created_at.date()}"



class PaymentLog(models.Model):
    """Logs payment transactions for annual subscriptions."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=6, decimal_places=2)  # e.g., 99.99
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    discount_applied = models.CharField(max_length=100, blank=True, null=True, default="None")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} (${self.amount}) - {self.status}"












