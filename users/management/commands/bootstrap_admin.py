from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import sys

User = get_user_model()

class Command(BaseCommand):
    help = "Quickly bootstraps your very first Master Admin account for the users application."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("--- Admin Account Bootstrapper ---"))
        
        username = input("Enter Admin Username: ").strip()
        if not username:
            raise CommandError("Username cannot be left blank.")
            
        if User.objects.filter(username=username).exists():
            raise CommandError(f"A user named '{username}' already exists in your database.")

        email = input("Enter Admin Email: ").strip()
        
        # Secure password input tracking
        import getpass
        password = getpass.getpass("Enter Admin Password: ")
        password_confirm = getpass.getpass("Confirm Admin Password: ")
        
        if password != password_confirm:
            raise CommandError("Passwords do not match. Aborting installation.")

        try:
            # Generate the user entry leveraging our custom model flags
            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_admin_member=True,
                is_staff=True,       # Grants core Django backend permission access
                is_superuser=True    # Grants full database administrative control
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully generated Master Admin: {admin_user.username} 🎉")
            )
            self.stdout.write(
                self.style.WARNING("You can now log into your dashboards or the /admin/ backend portal.")
            )
            
        except Exception as error:
            raise CommandError(f"Failed to write admin profile to database: {error}")
