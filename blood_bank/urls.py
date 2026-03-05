"""
URL configuration for blood_bank project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Session-based web views
    path("users/", include("users.urls", namespace="users")),
    path("donors/", include("donors.urls", namespace="donors")),
    path("hospitals/", include("hospitals.urls", namespace="hospitals")),
    path("inventory/", include("inventory.urls", namespace="inventory")),
    path("donations/", include("donations.urls", namespace="donations")),
    path("requests/", include("requests.urls", namespace="requests")),
    path("fraud/", include("fraud.urls", namespace="fraud")),
    path("audit/", include("audit.urls", namespace="audit")),
    # REST API routes
    path("api/", include("users.api_urls")),
    path("api/", include("blood_bank.api_urls")),
    # Root redirect
    path("", RedirectView.as_view(url="/users/login/", permanent=False), name="home"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
