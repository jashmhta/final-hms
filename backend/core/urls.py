from django.urls import path
from .views import HealthCheckView, root_api_view
urlpatterns = [
    path("", root_api_view, name="root"),
    path("health/", HealthCheckView.as_view(), name="health"),
]