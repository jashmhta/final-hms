"""Blood Bank URLs"""

from django.urls import include, path

urlpatterns = [
    path("", include("blood_bank.urls")),
]
