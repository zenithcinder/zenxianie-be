from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.LogoutView.as_view()),
    path('logout-all/', views.LogoutAllView.as_view()),
] 