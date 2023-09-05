from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """serializer for recipes"""
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'price', 'time_minutes', 'link']
        read_only_fields = ("id",)
        
class RecipeDetailSerializer(RecipeSerializer):
    """serializer for recipe detail view."""
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
