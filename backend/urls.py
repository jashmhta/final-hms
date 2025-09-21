from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rest_framework.urls")),
    path(
        "health/",
        lambda request: JsonResponse({"status": "healthy", "service": "HMS Backend"}),
    ),
]


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "HMS Backend", "version": "1.0.0"})
