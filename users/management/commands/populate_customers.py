from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import UserSubscription, PaymentLog, SubscriptionAuditLog
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "Generates mock customer accounts with realistic subscription tracking logs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--total', 
            type=int, 
            default=10, 
            help='Indicates the number of dummy customer profiles to generate.'
        )

    def handle(self, *args, **options):
        total = options['total']
        self.stdout.write(self.style.MIGRATE_HEADING(f"--- Bulk Populating {total} Customers ---"))

        # Base list of mock names to construct profiles randomly
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Jamie", "Riley", "Cameron", "Rees", "Skyler"]
        last_names = ["Smith", "Johnson", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Thomas", "White", "Lee"]

        count_created = 0
        now = timezone.now()

        for i in range(total):
            # 1. Generate unique matching credentials 
            f_name = random.choice(first_names)
            l_name = random.choice(last_names)
            random_suffix = random.randint(100, 999)
            
            username = f"{f_name.lower()}{random_suffix}"
            email = f"{username}@example-sandbox.com"
            
            # Skip if username衝突 overlaps an existing profile entry row
            if User.objects.filter(username=username).exists():
                continue

            # 2. Build the core customer shell record
            customer = User.objects.create_user(
                username=username,
                email=email,
                password="password123", # Uniform password for easy developer test logins
                first_name=f_name,
                last_name=l_name,
                is_customer=True
            )

            # 3. Randomize account subscription health to mix up dashboard views
            # 70% active subscribers, 30% inactive/expired
            is_active_status = random.random() < 0.70 
            
            if is_active_status:
                # Active: starts recently, ends standard 365 days out
                start = now - timedelta(days=random.randint(1, 100))
                end = start + timedelta(days=365)
            else:
                # Expired: started long ago, already passed its limit timeline
                start = now - timedelta(days=random.randint(370, 450))
                end = start + timedelta(days=365)

            # 4. Inject subscription record entry into database storage engines
            sub = UserSubscription.objects.create(
                user=customer,
                start_date=start,
                end_date=end,
                is_active=is_active_status
            )

            # 5. Connect matching invoice history lines
            txn_id = f"TXN-MOCK{random.randint(10000, 99999)}"
            PaymentLog.objects.create(
                subscription=sub,
                amount=99.99,
                transaction_id=txn_id,
                status='completed',
                created_at=start
            )

            # 6. Drop baseline administrative setup audit trail log trace elements
            SubscriptionAuditLog.objects.create(
                customer=customer,
                performed_by=None, # System action indicator flag label element
                action='activated' if is_active_status else 'deactivated',
                notes=f"Bulk environment bootstrap seed setup generation row logic pipeline (Initial entry)."
            )

            count_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully populated database with {count_created} mock customers! 🎉")
        )
        self.stdout.write(
            self.style.WARNING("All generated user passwords are standard: 'password123' for manual test logins.")
        )
