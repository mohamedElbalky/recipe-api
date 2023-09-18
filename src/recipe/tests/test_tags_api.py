from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def create_user(email="test@example.com", password="test123"):
    """create and return a new user"""
    return get_user_model().objects.create_user(email=email, password=password)

def create_tag(user, **kwargs):
    """create new tag by default prams"""
    default = {
        "name": "tag name"
    }
    default.update(kwargs)
    tag = Tag.objects.create(user=user, **default)
    return tag

class PublicTagApiTest(TestCase):
    """test unauthenticated api requests"""
    def setUp(self) -> None:
        self.client = APIClient()
        
    def test_auth_required(self) -> None:
        """test auth required for retriving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    
class PrivateTagApiTest(TestCase):
    """test authenticated api requests"""
    
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
        
    def test_retrive_tags(self) -> None:
        """test retrive a list for tags"""
        for i in range(5):
            create_tag(user=self.user, name=f"test tag{i}")
        
        tags = Tag.objects.order_by('-name')
        serializer = TagSerializer(tags, many=True)
        
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
    def test_retrive_tags_for_user(self) -> None:
        """test tags are retriving for the authenticated user"""

        
        new_user = create_user(email="new@examp.com", password="newuserpass123")
        create_tag(new_user)
        
        user_tag = create_tag(user=self.user, name="auth user tag")

        res = self.client.get(TAGS_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        
        for k, v in res.data[0].items():
            self.assertEqual(getattr(user_tag, k), v)
        
        