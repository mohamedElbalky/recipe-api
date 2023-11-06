from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register("recipes", views.RecipeViewSet)
router.register("tags", views.TagViewSet)
router.register("ingredients", views.IngredientViewSet)



app_name = "recipe"


urlpatterns = [
    # ViewSets endpoints
    path('', include(router.urls)),
    
    
    # FBV endpoints
    path('fbv/recipes/', views.recipe_view, name="recipe-list"),
    path('fbv/recipes/<str:recipe_id>/', views.recipe_detail_view, name="recipe-detail"),
    
    path('fbv/tags/', views.tag_view, name='tag-list'),
    path('fbv/tag/<int:tag_id>/', views.tag_detail_view, name="tag-detail"),
    
    path('fbv/ingredients/', views.ingredient_view, name="ingredient-list"),
    path('fbv/ingredients/<int:ingredient_id>/', views.ingredient_detail_view, name="ingredient-detail"),
    
    
]
