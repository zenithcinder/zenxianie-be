from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter(trailing_slash=True)
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.ProfileViewSet, basename='profile')

urlpatterns = router.urls

# Authentication endpoints
urlpatterns += [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view()),
    path('refresh-token/', views.UserLoginView.as_view()),  # Using UserLoginView for token refresh
    path('change-password/', views.ChangePasswordView.as_view()),
    path('users/', views.UserListView.as_view()),
    path('profile/', views.ProfileView.as_view()),
] 