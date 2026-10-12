from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSubscription, SubscriptionAuditLog, PaymentLog

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('Role Configuration', {'fields': ('is_customer', 'is_staff_member', 'is_admin_member', 'bio', 'phone_number')}),
    )

admin.site.register(User, CustomUserAdmin)


class UserSubscriptionAdmin(admin.ModelAdmin):
    # This creates clear, filterable columns on your list table screen
    list_display = ('get_username', 'is_active', 'end_date')

    # Helper method to safely pull the username from the related User model
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'  # Sets the column header title

# Register the model alongside the configuration class
admin.site.register(UserSubscription, UserSubscriptionAdmin)\


class SubscriptionAuditLogAdmin(admin.ModelAdmin):
    list_display = ('customer', 'performed_by', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    readonly_fields = ('customer', 'performed_by', 'action', 'notes', 'created_at')

# 3. CRUCIAL: Pass the Admin configuration class (SubscriptionAuditLogAdmin) as the second argument
admin.site.register(SubscriptionAuditLog, SubscriptionAuditLogAdmin)


from .models import PaymentLog

class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'transaction_id', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('subscription', 'amount', 'transaction_id', 'status', 'created_at')

    def get_username(self, obj):
        return obj.subscription.user.username
    get_username.short_description = 'Customer'

admin.site.register(PaymentLog, PaymentLogAdmin)

  

