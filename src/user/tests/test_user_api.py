from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**kwargs):
    """create new return a new user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserAPITest(TestCase):
    """test the public feature of the user api"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_succesful(self):
        """test create new user"""
        payload = {
            "email": "momo@example.com",
            "password": "example123",
            "name": "mohamed",
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_email_exists_error(self):
        """test error returned if user with email exists"""
        payload = {
            "email": "momo@example.com",
            "password": "example123",
            "name": "mohamed",
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """test an error is returned if password is less than 5 chars"""
        payload = {"email": "momo@example.com", "password": "ex", "name": "mohamed"}
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """test success create user token"""
        user_details = {
            "name": "mohamed",
            "email": "test@example.com",
            "password": "test123",
        }
        create_user(**user_details)
        pay_load = {
            "email": user_details["email"],
            "password": user_details["password"],
        }

        res = self.client.post(TOKEN_URL, pay_load)
        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_bad_token_credantails(self):
        """test return error if credantails invalid"""
        user_details = {
            "name": "mohamed",
            "email": "test@example.com",
            "password": "test123",
        }
        create_user(**user_details)
        pay_load = {"email": user_details["email"], "password": "123"}
        res = self.client.post(TOKEN_URL, pay_load)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_autherized(self):
        """Test authentication is required for user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivetUserApiTest(TestCase):
    """test api resquests that required authentication"""

    def setUp(self):
        user_data = {
            "email": "momo@example.com",
            "name": "example",
            "password": "example123",
        }
        self.user = create_user(**user_data)

        self.client = APIClient()

        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        """test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"email": self.user.email, "name": self.user.name})

    def test_post_me_is_not_allowed(self):
        """test post is not allowed for me endpoint"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """test updating user profile teh authenticated user"""
        payload = {"name": "uploaded name", "password": "test123test"}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
