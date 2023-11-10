from decimal import Decimal

import tempfile
import os

from PIL import Image

from rest_framework.test import APIClient
from rest_framework import status

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])

def image_upload_url(recipe_id):
    """Create and return an image detail url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a simple recipe"""
    defaults = {
        "title": "test recipe",
        "price": Decimal("4.21"),
        "time_minutes": 15,
        "description": "Simple test recipe description",
        "link": "https://example.com/recipe.pdf",
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
        self.user = create_user(
            email="example@example.com", password="test123", name="momo"
        )
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
            "price": Decimal("4.21"),
            "time_minutes": 15,
            "link": "https://example.com/recipe.pdf",
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
        recipe = create_recipe(user=self.user, title="simple recipe title", link=link)
        payload = {"title": "updated title"}
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
            description="recipe desc",
        )

        payload = {
            "title": "test recipe",
            "price": Decimal("4.21"),
            "time_minutes": 15,
            "description": "Simple test recipe description",
            "link": "https://example.com/recipe.pdf",
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
        payload = {"user": new_user}
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

    def test_create_recipe_with_new_tags(self):
        """test creat a recipe with new tags"""
        payload = {
            "title": "test recipe",
            "price": Decimal("4.21"),
            "time_minutes": 15,
            "tags": [{"name": "new tag number one"}, {"name": "new tag number two"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload["tags"]:
            exists = recipe.tags.filter(user=self.user, name=tag["name"]).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_exists_tag(self):
        """test create a recipe with exists tags"""
        tag = Tag.objects.create(name="existing tag", user=self.user)
        payload = {
            "title": "test recipe",
            "price": Decimal("4.21"),
            "time_minutes": 15,
            "tags": [{"name": "existing tag"}, {"name": "new tag number two"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(user=self.user, name=tag["name"]).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """test creating tag when updating the recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "test tag"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        test_tag = Tag.objects.get(user=self.user, name="test tag")
        self.assertIn(test_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """test assigning an existing tag when updating a tag"""
        tag_one = Tag.objects.create(name="tag one", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_one)

        tag_two = Tag.objects.create(name="tag two", user=self.user)

        payload = {"tags": [{"name": "tag two"}]}
        url = detail_url(recipe.id)
        ser = self.client.patch(url, payload, format="json")

        self.assertEqual(ser.status_code, status.HTTP_200_OK)

        self.assertIn(tag_two, recipe.tags.all())
        self.assertNotIn(tag_one, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """test clearing a recipy tags"""

        tag = Tag.objects.create(user=self.user, name="test tag")
        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag)

        url = detail_url(recipe.id)

        payload = {"tags": []}

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredient(self):
        """test create a rcipe with new tag"""
        paylaod = {
            "title": "test recipe",
            "price": Decimal("4.21"),
            "time_minutes": 15,
            "ingredients": [{"name": "test ing1"}, {"name": "test ing2"}],
        }

        res = self.client.post(RECIPES_URL, paylaod, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in paylaod["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user, name=ingredient["name"]
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """test create a new recipe with existing ingredient"""
        ing = Ingredient.objects.create(name="test ing", user=self.user)
        payload = {
            "title": "test recipe",
            "price": Decimal("2.12"),
            "time_minutes": 18,
            "ingredients": [{"name": "test ing"}, {"name": "test ing2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ing, recipe.ingredients.all())

        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                user=self.user, name=ingredient["name"]
            ).exists()

            self.assertTrue(exists)

    def test_recipe_ingredient_name_validation(self):
        """test ingredient name length must greater that 3"""
        payload = {
            "title": "test recipe",
            "price": Decimal("2.12"),
            "time_minutes": 18,
            "ingredients": [{"name": "te"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ingredient_on_update_recipe(self):
        """test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "test ing"}]}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ing = Ingredient.objects.get(name="test ing", user=self.user)
        self.assertIn(ing, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """test assigning an existing ingredient when updating a recipe with new ingredient"""

        ingredient1 = Ingredient.objects.create(user=self.user, name="test ing1")

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name="test ing2")

        payload = {"ingredients": [{"name": "test ing2"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient1, recipe.ingredients.all())
        self.assertIn(ingredient2, recipe.ingredients.all())

    def test_clear_recipe_ingredient(self):
        """test clearing a recipe ingredients"""
        ingredient = Ingredient.objects.create(user=self.user, name="test ing")

        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.delete(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_add_recipe_ingredient_created_by_another_auth_user(self):
        """test add ingredient to recipe, this ingredient created by another auth user"""

        another_user = create_user(email="otheruser@example.com", password="pass123@")
        another_user_ingredient = Ingredient.objects.create(
            user=another_user, name="another user ing"
        )
        
        auth_user_recipe = create_recipe(user=self.user)
        payload = {
            "ingredients": [{"name": "another user ing"}]
        }
        
        url = detail_url(auth_user_recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        ing = auth_user_recipe.ingredients.first()

        self.assertEqual(ing, another_user_ingredient)
        
        # self.assertIn(another_user_ingredient, auth_user_recipe.ingredients.all())
        

class ImageUploadTests(TestCase):
    """test upload recipe image"""

    def setUp(self):
        """excute before every testcase"""
        self.client = APIClient()
        self.user = create_user(email="test@example.xyz", password="test123")
        
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        """excute after every testcase"""
        self.recipe.image.delete()
        
    def test_upload_an_image(self):
        """Test upload an image to a recipe"""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                'image': image_file
            }
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        print(self.recipe.image.url)
        # self.assertTrue(os.path.exists(self.recipe.image.url))
            
    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {
            "image": "nothing"
        }
        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)