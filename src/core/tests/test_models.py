"""
    Test models
"""

from django.test import TestCase

from django.contrib.auth import get_user_model


def create_new_user(email, password):
    user = get_user_model().objects.create_user(email=email, password=password)
    return user


class TestCoreModel(TestCase):
    """Test Core Model"""
    def test_create_user_successful(self):
        """test create new user"""
        email = "momo@example.com"
        password = "momo123"
        user = create_new_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        
    def test_new_user_email_normalized(self):
        """test email is normalized for the new user"""
        email = 'test@EXAMPLE.COM'
        user = create_new_user(email=email, password="example123")
        self.assertEqual(user.email, email.lower())

    def test_new_user_without_email_raises_error(self):
        """test raise error when tring create user without email"""
        with self.assertRaises(ValueError):
            create_new_user(email="", password="example123")
            
    def test_create_superuser_successful(self):
        superuser = get_user_model().objects.create_superuser(
            email = "momo@example.com",
            password = "example123"
        )
        self.assertEqual(superuser.email, "momo@example.com")
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        