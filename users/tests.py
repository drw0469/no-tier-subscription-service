from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import User, UserSubscription, SubscriptionAuditLog, PaymentLog

class SubscriptionSystemTests(TestCase):

    def setUp(self):
        """Sets up baseline mock users for the test execution threads."""
        self.admin_user = User.objects.create_user(
            username="admin_test", email="admin@test.com", password="password123", is_admin_member=True
        )
        self.staff_user = User.objects.create_user(
            username="staff_test", email="staff@test.com", password="password123", is_staff_member=True
        )
        self.customer_user = User.objects.create_user(
            username="customer_test", email="customer@test.com", password="password123", is_customer=True
        )

    # ==============================================================================
    # 1. TEST CORE MODEL LOGIC
    # ==============================================================================
    def test_subscription_automatic_end_date_calculation(self):
        """Verifies that saving a subscription automatically calculates an end date 365 days out."""
        subscription = UserSubscription.objects.create(user=self.customer_user, is_active=True)
        
        # Verify the end date was calculated automatically
        self.assertIsNotNone(subscription.end_date)
        
        # Ensure it falls exactly 365 days past the start date
        expected_end_date = subscription.start_date + timedelta(days=365)
        self.assertAlmostEqual(subscription.end_date, expected_end_date, delta=timedelta(seconds=2))
        self.assertTrue(subscription.has_valid_access)

    # ==============================================================================
    # 2. TEST ROLE & ROUTER ACCESS
    # ==============================================================================
    def test_dashboard_router_redirects_correct_roles(self):
        """Ensures the central dashboard router sends different roles to their specific workspaces."""
        # Test Customer Routing
        self.client.login(username="customer_test", password="password123")
        response = self.client.get(reverse('dashboard_router'))
        self.assertRedirects(response, reverse('customer_dashboard'))
        self.client.logout()

        # Test Admin Routing
        self.client.login(username="admin_test", password="password123")
        response = self.client.get(reverse('dashboard_router'))
        self.assertRedirects(response, reverse('admin_dashboard'))

    # ==============================================================================
    # 3. TEST THE "AUDIT TRAIL" COMPROMISE LOGIC
    # ==============================================================================
    def test_toggle_subscription_creates_audit_log_and_saves(self):
        """Verifies staff can successfully activate a customer and that an audit trail is written."""
        self.client.login(username="staff_test", password="password123")
        
        # Trigger the post toggle route with mandatory notes
        url = reverse('toggle_subscription', kwargs={'user_id': self.customer_user.id})
        response = self.client.post(url, {
            'action_type': 'activate',
            'reason_notes': 'Customer paid cash at the counter.'
        })
        
        # Check for clean redirect response
        self.assertEqual(response.status_code, 302)
        
        # Check database to see if customer is now active
        subscription = UserSubscription.objects.get(user=self.customer_user)
        self.assertTrue(subscription.is_active)
        
        # Verify an unalterable audit log row was written perfectly
        audit_exists = SubscriptionAuditLog.objects.filter(
            customer=self.customer_user,
            performed_by=self.staff_user,
            action='activated',
            notes='Customer paid cash at the counter.'
        ).exists()
        self.assertTrue(audit_exists)

    def test_toggle_subscription_fails_without_reason_notes(self):
        """Verifies that missing reason notes halts execution and leaves database untouched."""
        self.client.login(username="staff_test", password="password123")
        
        url = reverse('toggle_subscription', kwargs={'user_id': self.customer_user.id})
        response = self.client.post(url, {
            'action_type': 'activate',
            'reason_notes': '' # Empty text input string
        })
        
        # Ensure subscription record stays false default state
        subscription_exists = UserSubscription.objects.filter(user=self.customer_user, is_active=True).exists()
        self.assertFalse(subscription_exists)

    # ==============================================================================
    # 4. TEST SECURITY & "LOGIN-AS" PROFILE WRITE BLOCKS
    # ==============================================================================
    def test_impersonation_mode_locks_profile_mutations(self):
        """Guarantees that an operator cannot submit profile edit modifications while impersonating a customer."""
        # 1. Log in as staff and trigger impersonation session tracking keys
        self.client.login(username="staff_test", password="password123")
        impersonate_url = reverse('impersonate_user', kwargs={'user_id': self.customer_user.id})
        self.client.get(impersonate_url) # Session is transformed
        
        # 2. Try to submit a profile change request while impersonating
        edit_url = reverse('edit_user_profile', kwargs={'user_id': self.customer_user.id})
        response = self.client.post(edit_url, {
            'first_name': 'HackedName',
            'last_name': 'Test',
            'email': 'customer@test.com'
        })
        
        # 3. Refresh user object from database and verify the name change was BLOCKED
        self.customer_user.refresh_from_db()
        self.assertNotEqual(self.customer_user.first_name, 'HackedName')
        self.assertRedirects(response, reverse('customer_dashboard'))
