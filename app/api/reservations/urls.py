from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter(trailing_slash=True)
router.register(r'reservations', views.ReservationViewSet, basename='reservation')

urlpatterns = router.urls

# Additional endpoints
urlpatterns += [
    # User specific endpoints
    path('reservations/my/', views.ReservationViewSet.as_view({'get': 'my_reservations'})),
    path('reservations/active/', views.ReservationViewSet.as_view({'get': 'active'})),
    path('reservations/<int:pk>/cancel/', views.ReservationViewSet.as_view({'post': 'cancel'})),
]

# Admin endpoints
urlpatterns += [
    path('reservations/<int:pk>/status/', views.ReservationViewSet.as_view({'patch': 'update_status'})),
] 