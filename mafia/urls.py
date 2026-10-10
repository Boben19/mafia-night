from django.contrib import admin
from django.urls import path, include
from game.views import guest_login
urlpatterns = [path("admin/", admin.site.urls), path("accounts/guest/", guest_login, name="guest"), path("accounts/", include("allauth.urls")), path("", include("game.urls"))]
