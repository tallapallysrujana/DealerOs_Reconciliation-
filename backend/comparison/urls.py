from django.urls import path, include
from rest_framework.routers import DefaultRouter
from comparison.views import DisagreementViewSet

router = DefaultRouter()
router.register(r'disagreements', DisagreementViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]