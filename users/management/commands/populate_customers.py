from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import UserSubscription, PaymentLog, SubscriptionAuditLog
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "Generates mock customer and specialized test executive accounts with realistic subscription tracking logs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--total', 
            type=int, 
            default=10, 
            help='Indicates the number of dummy customer profiles to generate.'
        )
        # ADDED: Explicit control tracking flag parameters for stakeholder profiles
        parser.add_argument(
            '--executives',
            type=int,
            default=2,
            help='Indicates the number of specialized test executive account profiles to generate.'
        )

    def handle(self, *args, **options):
        total_customers = options['total']
        total_executives = options['executives']
        now = timezone.now()

        # ==============================================================================
        # PHASE 1: GENERATE SPECIALIZED EXECUTIVE STAKEHOLDERS
        # ==============================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- Bulk Populating {total_executives} Executive Accounts ---"))
        exec_count = 0
        
        for e in range(total_executives):
            username = f"exec_partner{random.randint(10, 99)}"
            email = f"{username}@company-stakeholder.com"

            if User.objects.filter(username=username).exists():
                continue

            User.objects.create_user(
                username=username,
                email=email,
                password="password123", # Uniform credentials for easy testing
                first_name="Exec",
                last_name=f"Partner #{e+1}",
                is_executive_member=True, # Flipping the newly created role flag box matrix
                is_staff=False,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS(f"  • Created Executive Account: {username}"))
            exec_count += 1

        # ==============================================================================
        # PHASE 2: GENERATE STANDARD CUSTOMER LOG DIRECTORIES
        # ==============================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n--- Bulk Populating {total_customers} Customer Accounts ---"))
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Jamie", "Riley", "Cameron", "Rees", "Skyler"]
        last_names = ["Smith", "Johnson", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Thomas", "White", "Lee"]
        cust_count = 0

        for i in range(total_customers):
            f_name = random.choice(first_names)
            l_name = random.choice(last_names)
            random_suffix = random.randint(100, 999)
            
            username = f"{f_name.lower()}{random_suffix}"
            email = f"{username}@example-sandbox.com"
            
            if User.objects.filter(username=username).exists():
                continue

            customer = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                first_name=f_name,
                last_name=l_name,
                is_customer=True
            )

            # Randomize account health (70% active subscribers, 30% naturally expired)
            is_active_status = random.random() < 0.70 
            
            if is_active_status:
                start = now - timedelta(days=random.randint(1, 100))
                end = start + timedelta(days=365)
            else:
                start = now - timedelta(days=random.randint(370, 450))
                end = start + timedelta(days=365)

            sub = UserSubscription.objects.create(
                user=customer,
                start_date=start,
                end_date=end,
                is_active=is_active_status
            )

            # Randomize billing entries to simulate full-price vs discounted invoices
            # 80% Full Price, 15% Partial Discounts, 5% Comped accounts
            rand_billing = random.random()
            if rand_billing < 0.80:
                final_price = 99.99
                discount_text = "None"
            elif rand_billing < 0.95:
                final_price = 79.99
                discount_text = "20% Promotional Loyalty Discount"
            else:
                final_price = 0.00
                discount_text = "100% Free Administrative Complimentary Account"

            PaymentLog.objects.create(
                subscription=sub,
                amount=final_price,
                transaction_id=f"TXN-MOCK{random.randint(10000, 99999)}",
                status='completed',
                discount_applied=discount_text,
                created_at=start
            )

            SubscriptionAuditLog.objects.create(
                customer=customer,
                performed_by=None,
                action='activated' if is_active_status else 'deactivated',
                notes=f"Bulk database bootstrap generation seed engine matrix profile setup."
            )

            cust_count += 1

        # Final terminal status report card summary metrics output lines
        self.stdout.write(self.style.SUCCESS(f"\nExecution Complete: Successfully injected {exec_count} Executive and {cust_count} Customer entries! 🎉"))
        self.stdout.write(self.style.WARNING("All generated profile account passwords are uniformly set to: 'password123'"))
