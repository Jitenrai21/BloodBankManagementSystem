from django.urls import path
from .api_views import RegisterAPIView, LoginAPIView, LogoutAPIView, MeAPIView

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="api_register"),
    path("auth/login/", LoginAPIView.as_view(), name="api_login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="api_logout"),
    path("auth/me/", MeAPIView.as_view(), name="api_me"),
]
