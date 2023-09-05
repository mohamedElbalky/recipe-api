from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.contrib import admin
from django.urls import path, include



schema_view = get_schema_view(
    openapi.Info(
        title="Recipe API",
        default_version='v1',
        description="Recipe API",
        ),
        # public=True,
        # permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # admin pannal path
    path("admin/", admin.site.urls),

    # api documentaion path
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    
    # user api app
    path("api/user/", include("user.urls")),
    
    # recipe api app
    path('api/recipe/', include('recipe.urls')),
]
