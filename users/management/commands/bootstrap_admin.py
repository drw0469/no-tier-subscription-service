from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import sys

User = get_user_model()

class Command(BaseCommand):
    help = "Quickly bootstraps your choice of a Master Admin or a Business Executive account for the application."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("--- Internal System Account Provisioner ---"))
        
        # 1. Capture the structural target role profile choice type
        self.stdout.write("\nSelect Account Privilege Level:")
        self.stdout.write("  [1] Master Admin (Full System Control & Database Modifications)")
        self.stdout.write("  [2] Business Executive (Read-Only Financial Logs & Revenue Analytics View)")
        role_choice = input("Enter choice (1 or 2): ").strip()
        
        if role_choice not in ['1', '2']:
            raise CommandError("Invalid selection. Installation aborted.")

        # 2. Capture core identification variables
        username = input("\nEnter Target Username: ").strip()
        if not username:
            raise CommandError("Username cannot be left blank.")
            
        if User.objects.filter(username=username).exists():
            raise CommandError(f"A user named '{username}' already exists in your database directory.")

        email = input("Enter Email Address: ").strip()
        
        # 3. Secure password input loops
        import getpass
        password = getpass.getpass("Enter Account Password: ")
        password_confirm = getpass.getpass("Confirm Account Password: ")
        
        if password != password_confirm:
            raise CommandError("Passwords do not match. Aborting installation framework.")

        try:
            # 4. Map the logical role control parameters parameters
            if role_choice == '1':
                # Master Admin Role Flags Set Up
                admin_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_admin_member=True,
                    is_executive_member=False,
                    is_staff=True,       # Grants core Django backend visibility permissions
                    is_superuser=True    # Grants full root database admin control
                )
                success_message = f"\nSuccessfully generated Master Admin: {admin_user.username} 🎉"
                warning_message = "You can now log into your dashboards or the /admin/ core backend portal."
            
            else:
                # Business Executive Role Flags Set Up
                exec_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_executive_member=True, # Toggles the newly deployed analytical role flag
                    is_admin_member=False,
                    is_staff=False,           # Keeps them completely locked out of the core database tables
                    is_superuser=False
                )
                success_message = f"\nSuccessfully generated Business Executive: {exec_user.username} 📊"
                warning_message = "They can now log into the frontend portal to review financial analytics views."

            self.stdout.write(self.style.SUCCESS(success_message))
            self.stdout.write(self.style.WARNING(warning_message))
            
        except Exception as error:
            raise CommandError(f"Failed to write internal identity profile record to database: {error}")
