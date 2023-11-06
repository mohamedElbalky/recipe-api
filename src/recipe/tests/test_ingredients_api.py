from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient


from core.models import Recipe, Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")

def detail_url(ingredient_id):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def detail_url(ingredient_id):
    """create and return ingredient"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="test@example.xyz", password="test123"):
    """create and return user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTest(TestCase):
    """test unauthenticated api requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth is required for retriving ingredients"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """test authenticated api requests"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()

        self.client.force_authenticate(user=self.user)

    def test_retrive_ingredients(self):
        """test list ingredients"""
        Ingredient.objects.create(name="ing one", user=self.user)
        Ingredient.objects.create(name="ing two", user=self.user)
        ings = Ingredient.objects.all().order_by("-name")
        
        ser = IngredientSerializer(ings, many=True)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, ser.data)
        
    def test_ingredients_limted_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        new_user = create_user(email="newuser@example.com", password="newuser123")
        Ingredient.objects.create(name="new user ing", user=new_user)
        
        ing = Ingredient.objects.create(name="auth user ing", user=self.user)
        
        ings = Ingredient.objects.all().filter(user=self.user).order_by("-name")
        
        ser = IngredientSerializer(ings, many=True)

        res = self.client.get(INGREDIENTS_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, ser.data)
        self.assertEqual(res.data[0]["name"], ing.name)
        
    def test_create_ingedient_successful(self):
        """test create a new ingredient"""
        payload = {"name": "test ing"}
        res = self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(user=self.user, name=payload["name"]).exists()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)
        
    def test_create_ingredient_invalid(self):
        """test create invalid ingredient fails"""
        payload = {"name": ""}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_update_ingedient(self):
        """test update an ingredient"""
        ing = Ingredient.objects.create(name="test ing", user=self.user)

        payload = {"name": "updated ing"}
        url = detail_url(ing.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ing.refresh_from_db()

        self.assertEqual(ing.name, payload["name"])
        
    def test_delete_ingredient(self):
        """test delete an ingredient"""
        ing = Ingredient.objects.create(name="test ing", user=self.user)
        
        url = detail_url(ing.id)
        res = self.client.delete(url)
        
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        exists = Ingredient.objects.filter(user=self.user).exists()
        self.assertFalse(exists)
        
    def test_ingredient_name_validation(self):
        """test ingredient name length must greater that 3"""
        payload = {
            "name": "te"
        }
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

