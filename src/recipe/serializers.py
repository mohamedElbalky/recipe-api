from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """serializer for tags"""

    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ["id"]

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("This name is very short")
        return value


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name")
        read_only_fields = ["id"]

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("This name is very short")
        return value


class RecipeSerializer(serializers.ModelSerializer):
    """serializer for recipes"""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ["id", "title", "price", "time_minutes", "link", "tags", "ingredients"]
        read_only_fields = ("id",)

    def _get_or_create_tags(self, tags, recipe):
        """handle getting or creating tags as needed"""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)

    # def _get_or_create_ingredients(self, ingredients, recipe):
    #     """handle getting or creating ingredients as needed"""
    #     auth_user = self.context["request"].user
    #     for ingredient in ingredients:
    #         ingredient_obj, created = Ingredient.objects.get_or_create(
    #             user=auth_user, **ingredient
    #         )
    #         recipe.ingredients.add(ingredient_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """
        handle getting or creating ingredients as needed,
        when using ingredient from anther users
        """
        auth_user = self.context["request"].user
        for ing in ingredients:
            try:
                ing_obj = Ingredient.objects.get(**ing)
            except Ingredient.DoesNotExist:
                ing_obj = Ingredient.objects.create(user=auth_user, **ing)
            finally:
                recipe.ingredients.add(ing_obj)

    def create(self, validated_data):
        """create a recipe with tags and ingredients"""
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """update a recipe with tags and ingredients"""
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description", "image"]


class RecipeImageSerializer(serializers.ModelSerializer):
    """
    serializer for uploading image to recipe,
    we add separate image serializer becouse it is best
    practice to only upload one type of data to an api
    """

    class Meta:
        model = Recipe
        fields = ("id", "image")
        read_only_fields = ("id",)
        extra_kwargs = {"image": {"required": "True"}}
