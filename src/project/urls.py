from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # admin pannal path
    path("admin/", admin.site.urls),
    # api documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/doc/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # user api app
    path("api/user/", include("user.urls")),
    # recipe api app
    path("api/recipe/", include("recipe.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )