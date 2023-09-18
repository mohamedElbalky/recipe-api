from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register("recipes", views.RecipeViewSet)
router.register("tags", views.TagViewSet)



app_name = "recipe"


urlpatterns = [
    # ViewSets endpoints
    path('', include(router.urls)),
    
    
    # FBV endpoints
    path('fbv/recipes/', views.recipe_view, name="recipe-list"),
    path('fbv/recipes/<str:recipe_id>/', views.recipe_detail_view, name="recipe-detail"),
    
    path('fbv/tags/', views.tag_view, name='tag-list'),
]
