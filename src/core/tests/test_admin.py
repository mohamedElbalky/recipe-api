"""
tests for the django admin modifications.
"""

from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class AdminSiteTests(TestCase):
    """Test Admin Site"""
    def setUp(self):
        """setUp test properties that applay in all test units"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="example@example.abc",
            password="example123"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="user123",
            name="test user"
        )
        
    def test_users_list_page(self):
        """test the users are lists in the page"""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)
        
    def test_edit_user_page(self):
        """test the edit user page works """
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        
    def test_add_user_page(self):
        """test add new user page works"""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
