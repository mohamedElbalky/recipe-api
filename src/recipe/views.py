from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view, 
    permission_classes, 
    authentication_classes
)
from rest_framework import status
from rest_framework.response import Response


from core.models import Recipe
from . import serializers



class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe api"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """Retrive recipes for authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """return a serializer class request.
            A viewset that provides default `create()`, `retrieve()`, `update()`, `partial_update()`, `destroy()` and `list()` actions.
        """
        if self.action == "list":
            return serializers.RecipeSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create new recipe"""
        serializer.save(user=self.request.user)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def recipe_view(request):
    """A view to list recipes"""
    if request.method == "GET":
        user = request.user
        recipes = Recipe.objects.filter(user=user).order_by("-id")
        ser = serializers.RecipeSerializer(recipes, many=True, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)
    
    elif request.method == "POST":
        ser = serializers.RecipeDetailSerializer(data=request.data, context={"request": request})
        if ser.is_valid(raise_exception=True):
            ser.save(user=request.user)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"error": "In-valid method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def recipe_detail_view(request, recipe_id=None):
    """A view to detail recipe"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
    except Http404:
        return Response({"error": "recipe not found"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "recipe ID is invalid"}, status=status.HTTP_404_NOT_FOUND)
    ser = serializers.RecipeDetailSerializer(recipe, context={"request": request})
    return Response(ser.data, status=status.HTTP_200_OK)
