from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    # Admin management
    path("manage/", views.manage_users, name="manage_users"),
    path("<int:pk>/approve/", views.approve_user, name="approve_user"),
    path("<int:pk>/block/", views.block_user, name="block_user"),
    path("<int:pk>/unblock/", views.unblock_user, name="unblock_user"),
]
