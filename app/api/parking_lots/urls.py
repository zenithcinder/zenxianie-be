from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=True)
router.register(r'parking-lots', views.ParkingLotViewSet, basename='parking-lot')
router.register(r'spaces', views.ParkingSpaceViewSet, basename='parking-space')

urlpatterns = router.urls

# Additional endpoints
urlpatterns += [
    # Parking lot specific endpoints
    path('parking-lots/<int:pk>/available-spaces/', views.ParkingLotViewSet.as_view({'get': 'available_spaces'})),
    path('parking-lots/<int:pk>/occupancy-rate/', views.ParkingLotViewSet.as_view({'get': 'occupancy_rate'})),
    path('parking-lots/search/', views.ParkingLotViewSet.as_view({'get': 'search'})),
    path('parking-lots/active/', views.ParkingLotViewSet.as_view({'get': 'active'})),
    path('parking-lots/with-available-spaces/', views.ParkingLotViewSet.as_view({'get': 'with_available_spaces'})),
    
    # Parking space specific endpoints
    path('spaces/<int:pk>/reserve/', views.ParkingSpaceViewSet.as_view({'post': 'reserve'})),
    path('spaces/<int:pk>/occupy/', views.ParkingSpaceViewSet.as_view({'post': 'occupy'})),
    path('spaces/<int:pk>/vacate/', views.ParkingSpaceViewSet.as_view({'post': 'vacate'})),
] 