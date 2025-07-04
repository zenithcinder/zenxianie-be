from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, ParkPointsViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'points', ParkPointsViewSet, basename='points')

urlpatterns = [
    path('', include(router.urls)),
] 