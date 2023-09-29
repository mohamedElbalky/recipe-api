from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework import status
from rest_framework.response import Response


from core.models import Recipe, Tag
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
        A viewset that provides default `create()`, `retrieve()`,
        `update()`, `partial_update()`, `destroy()` and `list()` actions.
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
        ser = serializers.RecipeSerializer(
            recipes, many=True, context={"request": request}
        )
        return Response(ser.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        ser = serializers.RecipeDetailSerializer(
            data=request.data, context={"request": request}
        )
        if ser.is_valid(raise_exception=True):
            ser.save(user=request.user)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"error": "In-valid method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["GET", "PATCH", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def recipe_detail_view(request, recipe_id=None):
    """A view to detail recipe"""
    data = request.data
    try:
        id = int(recipe_id)
    except ValueError:
        return Response(status=status.HTTP_404_NOT_FOUND)

    recipe = get_object_or_404(Recipe, id=id)

    if request.method == "GET":
        ser = serializers.RecipeDetailSerializer(recipe, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        # Don't update all data [part of data]
        ser = serializers.RecipeDetailSerializer(
            recipe, data=data, context={"request": request}, partial=True
        )
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "PUT":
        # update all data record
        ser = serializers.RecipeDetailSerializer(
            recipe, data=data, context={"request": request}
        )
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        # update recipe
        if recipe.user != request.user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """view for manage tag api"""

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user).order_by("-name")
        return qs


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def tag_view(request):
    """vew for mange tag list api and create new tag api"""
    if request.method == "GET":
        user = request.user
        tags = Tag.objects.filter(user=user).order_by("-name")
        ser = serializers.TagSerializer(tags, many=True, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        ser = serializers.TagSerializer(data=request.data, context={"request": request})
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH", "PUT", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def tag_detail_view(request, tag_id=None):
    """view for manage one tag"""
    data = request.data
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == "GET":
        ser = serializers.TagSerializer(tag, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        ser = serializers.TagSerializer(
            tag, data=data, context={"request": request}, partial=True
        )
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
