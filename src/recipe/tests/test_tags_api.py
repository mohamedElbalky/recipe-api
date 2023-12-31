from decimal import Decimal

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
    default = {"name": "tag name"}
    default.update(kwargs)
    tag = Tag.objects.create(user=user, **default)
    return tag


def tag_detail_url(tag_id):
    """reevrse to tag by id"""
    return reverse("recipe:tag-detail", args=[tag_id])


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

        tags = Tag.objects.order_by("-name")
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

    def test_retrive_one_tag_by_id(self):
        """test retrive one tag"""
        tag = create_tag(user=self.user)
        url = tag_detail_url(tag.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tag_update(self):
        """test update tag"""
        tag = create_tag(user=self.user, name="new tag")

        url = tag_detail_url(tag.id)
        payload = {"name": "updated tag"}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(res.data["name"], tag.name)

    def test_tag_delete(self):
        """test delete tag"""
        tag = create_tag(user=self.user)

        url = tag_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Tag.objects.count(), 0)

        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        """test listing tag by those assigned to recipe"""
        tag1 = Tag.objects.create(user=self.user, name="tag one")
        tag2 = Tag.objects.create(user=self.user, name="tag two")

        recipe = Recipe.objects.create(
            user=self.user, title="test recipe", price=Decimal("11.2"), time_minutes=13
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        ser1 = TagSerializer(tag1)
        ser2 = TagSerializer(tag2)

        self.assertIn(ser1.data, res.data)
        self.assertNotIn(ser2.data, res.data)

    def test_filter_tags_unique(self):
        """test filter tags returns a unique list"""
        tag1 = Tag.objects.create(user=self.user, name="tag onw")
        Tag.objects.create(user=self.user, name="tag two")

        recipe1 = Recipe.objects.create(
            user=self.user, title="test recipe1", price=Decimal("11.2"), time_minutes=13
        )
        recipe2 = Recipe.objects.create(
            user=self.user, title="test recipe2", price=Decimal("11.2"), time_minutes=13
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
