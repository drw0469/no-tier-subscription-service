from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import UserSubscription, SubscriptionAuditLog

class Command(BaseCommand):
    help = "Scans all active customer subscriptions and deactivates any that have passed their expiration end date."

    def handle(self, *args, **options):
        now = timezone.now()
        
        # 1. Fetch all subscriptions that are marked active but have expired
        expired_subs = UserSubscription.objects.filter(
            is_active=True,
            end_date__lt=now
        ).select_related('user')
        
        count = expired_subs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"[{now}] System Scan Complete: 0 subscriptions have expired."))
            return

        self.stdout.write(self.style.WARNING(f"[{now}] Processing Expirations: Found {count} expired profiles..."))

        # 2. Iterate and flip them while logging an automated audit row entry
        for subscription in expired_subs:
            customer_profile = subscription.user
            
            # Deactivate access
            subscription.is_active = False
            subscription.save(update_fields=['is_active'])

            # Log an automated system action to your audit trail logs database
            SubscriptionAuditLog.objects.create(
                customer=customer_profile,
                performed_by=None,  # None acts as "System" automatically in our __str__ model helper
                action='deactivated',
                notes=f"Automated background script execution: Subscription hit expiration timeline target ({subscription.end_date.strftime('%Y-%m-%d %H:%M:%S')})."
            )

            self.stdout.write(self.style.SUCCESS(f" - Successfully revoked access for account: {customer_profile.username}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed and updated {count} expired user records."))
