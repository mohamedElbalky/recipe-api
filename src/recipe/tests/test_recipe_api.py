from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse



from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)



RECIPES_URL = reverse("recipe:recipe-list")
# CREATE_RECIPE_URL = reverse("recipe:recipe-create")
# UPDATE_RECIPE_URL = reverse("recipe:update")

def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a simple recipe"""
    defaults = {
        "title": "test recipe",
        "price": Decimal('4.21'),
        "time_minutes": 15,
        "description": "Simple test recipe description",
        "link": "https://example.com/recipe.pdf"
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPIView(TestCase):
    """Test authenticated API requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test auth is required to call API"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):
    """test recipe endpoints"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="example@example.com", password="test123", name="momo")
        self.client.force_authenticate(self.user)
        
    def test_retrive_recipes(self):
        """test retrive a list of recipes"""
        for i in range(5):
            create_recipe(user=self.user)

        recipes = Recipe.objects.order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
    def test_recipe_list_limited_to_user(self):
        other_user = create_user(email="other@user.com", password="test123")
        
        create_recipe(user=other_user)
        create_recipe(user=self.user)
        
        auth_user_recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(auth_user_recipes, many=True)
        
        res = self.client.get(RECIPES_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)
        
    def test_get_recipe_detail(self):
        """test get recipe detail sucessful"""
        recipe = create_recipe(user=self.user)
        serializer = RecipeDetailSerializer(recipe)
        
        url = detail_url(recipe.id)
        res = self.client.get(url)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
    def test_recipe_detail_with_invalid_id_number_error(self):
        """test get recipe detail with invalid ID"""
        url = detail_url(12873)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_recipe_detail_with_invalid_id_text_error(self):
        """test get recipe detail with invalid ID"""
        url = detail_url("dsncdjn")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recipe(self):
        """test create new rercipe"""
        payload = {
            "title": "test recipe",
            "price": Decimal('4.21'),
            "time_minutes": 15,
            "description": "Simple test recipe description",
            "link": "https://example.com/recipe.pdf"
        }
        res = self.client.post(RECIPES_URL, payload)
        
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(res.data["title"], payload["title"])
        # self.assertEqual(res.data["title"], getattr(recipe, "title"))

        # recipe = Recipe.objects.get(id=res.data.get("id"))
        recipe = Recipe.objects.first()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """test recipe parial update"""
        link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="simple recipe title",
            link=link
        )
        payload = {
            "title": "updated title"
        }
        url = detail_url(recipe.id)
        
        res = self.client.patch(url, payload)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, link)
        self.assertEqual(recipe.user, self.user)
        
    def test_full_update(self):
        """test recipe full update[update all fields]"""
        recipe = create_recipe(
            user=self.user,
            title="new recipe",
            link="https://example.com/recipe.pdf",
            description="recipe desc"
        )
        
        payload = {
            "title": "test recipe",
            "price": Decimal('4.21'),
            "time_minutes": 15,
            "description": "Simple test recipe description",
            "link": "https://example.com/recipe.pdf"
        }
        
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        recipe.refresh_from_db()
        
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
        
    def test_update_user_recipe_return_error(self):
        """test change the recipe user return results in an error"""
        new_user = create_user(email="test@example.com", password="test123")
        
        recipe = create_recipe(user=self.user)
        payload = {
            "user": new_user
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        
    def test_delete_recipe(self):
        """test success delete recipe"""
        recipe = create_recipe(user=self.user)
        
        url = detail_url(recipe.id)
        
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
        
    def test_delete_other_user_recipe_return_error(self):
        """test tring to delete other users recipe gives error"""
        new_user = create_user(email="test@example.com", password="test123")
        recipe = create_recipe(user=new_user)
        
        url = detail_url(recipe.id)
        
        res = self.client.delete(url)
        
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())