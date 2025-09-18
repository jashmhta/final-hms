from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TallyIntegrationViewSet
router = DefaultRouter()
router.register(r'tally-integrations', TallyIntegrationViewSet, basename='tallyintegration')
urlpatterns = [
    path("", include(router.urls)),
]