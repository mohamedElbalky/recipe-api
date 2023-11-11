from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    action,
)

from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from core.models import Recipe, Tag, Ingredient
from . import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="comma separated list of tags ids to filter",
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="comma separated list of ingredients ids to filter",
            ),
        ],
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe api"""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def _params_to_ints(self, qs):
        """convert a list of strings to integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrive recipes for authenticated user"""
        # return self.queryset.filter(user=self.request.user).order_by("-id")

        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset

        if tags:
            tags_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)

        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):
        """return a serializer class request.
        A viewset that provides default `create()`, `retrieve()`,
        `update()`, `partial_update()`, `destroy()` and `list()` actions.
        """
        if self.action == "list":
            return serializers.RecipeSerializer
        elif self.action == "upload_image":
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by items assigned to recipes.",
            )
        ]
    )
)
class TagViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """view for manage tag api"""

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        assigned_only = bool(int(self.request.query_params.get("assigned_only")))
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        queryset = queryset.order_by("-name").distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by items assigned to recipes.",
            )
        ]
    )
)
class IngredientViewSet(viewsets.ModelViewSet):
    """view for manage ingredient api"""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """filter queryset to authenticate user"""
        # qs = self.queryset.filter(user=self.request.user).order_by("-name")
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = self.queryset.filter(user=self.request.user)
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        queryset = queryset.order_by("-name").distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -------------------------- FBV ---------------------------------------
# ----------------start help functions---------------------
def params_to_ints(qs):
    """convert string params to integer type"""
    return [int(str_id) for str_id in qs.split(",")]


def get_queryset(request, Klass):
    """filter queryset to authenticate user"""
    queryset = Klass.objects.filter(user=request.user)
    assigned_only = bool(int(request.query_params.get("assigned_only", 0)))
    if assigned_only:
        queryset = queryset.filter(recipe__isnull=False)
    queryset = queryset.order_by("-name").distinct()
    return queryset


# ------------------ end help functions -------------------


@extend_schema(
    request=serializers.RecipeDetailSerializer,
    responses=None,
    parameters=[
        OpenApiParameter(
            "tags",
            OpenApiTypes.STR,
            description="comma separated list of tags ids to filter",
        ),
        OpenApiParameter(
            "ingredients",
            OpenApiTypes.STR,
            description="comma separated list of ingredients ids to filter",
        ),
    ],
    methods=["GET"],
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def recipe_view(request):
    """A view to list recipes"""
    if request.method == "GET":
        user = request.user
        # recipes = Recipe.objects.filter(user=user).order_by("-id")
        recipes = Recipe.objects.all()
        tags = request.query_params.get("tags")
        ingredients = request.query_params.get("ingredients")
        if tags:
            tags_ids = params_to_ints(tags)
            recipes = recipes.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredients_ids = params_to_ints(ingredients)
            recipes = recipes.filter(ingredients__id__in=ingredients_ids)

        recipes = recipes.filter(user=user).order_by("-id").distinct()
        # print(recipes)
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


@extend_schema(request=serializers.RecipeImageSerializer, responses=None)
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@api_view(["POST"])
def recipe_image_view(request, recipe_id):
    """upload a recipe image view"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == "POST":
        ser = serializers.RecipeImageSerializer(recipe, request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=serializers.RecipeDetailSerializer, responses=None)
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


@extend_schema(
    request=serializers.TagSerializer,
    responses=None,
    methods=["GET"],
    parameters=[
        OpenApiParameter(
            "assigned_only",
            OpenApiTypes.INT,
            enum=[0, 1],
            description="Filter by items assigned to recipes.",
        )
    ],
)
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def tag_view(request):
    """vew for mange tag list api and create new tag api"""
    if request.method == "GET":
        queryset = get_queryset(request, Tag)
        ser = serializers.TagSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        ser = serializers.TagSerializer(data=request.data, context={"request": request})
        if ser.is_valid(raise_exception=True):
            ser.save(user=request.user)
            return Response(ser.data, status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=serializers.TagSerializer, responses=None)
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

    if request.method == "PUT":
        ser = serializers.TagSerializer(
            tag, data=request.data, context={"request": request}
        )
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=serializers.IngredientSerializer,
    responses=None,
    methods=["GET"],
    parameters=[
        OpenApiParameter(
            "assigned_only",
            OpenApiTypes.INT,
            enum=[0, 1],
            description="Filter by items assigned to recipes.",
        )
    ],
)
@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def ingredient_view(request):
    """function view for manage ingredient api ==> [list and create]"""
    if request.method == "GET":
        queryset = get_queryset(request, Ingredient)
        ser = serializers.IngredientSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "POST":
        ser = serializers.IngredientSerializer(
            data=request.data, context={"request": request}
        )
        if ser.is_valid():
            ser.save(user=request.user)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema(request=serializers.IngredientSerializer, responses=None)
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
@api_view(["GET", "PATCH", "PUT", "DELETE"])
def ingredient_detail_view(request, ingredient_id=None):
    """fbv for manage an ingredient ==> [retrive, update, delete]"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == "GET":
        ser = serializers.IngredientSerializer(ingredient, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        ser = serializers.IngredientSerializer(
            ingredient, data=request.data, context={"request": request}, partial=True
        )
        if ser.is_valid():
            ser.save(user=request.user)
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        ingredient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
