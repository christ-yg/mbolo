from django.urls import path

from .views import (
    CurrentProfileView,
    CurrentSearchPreferencesView,
)


app_name = "profiles"

urlpatterns = [
    path(
        "me/",
        CurrentProfileView.as_view(),
        name="current-profile",
    ),
    path(
        "preferences/me/",
        CurrentSearchPreferencesView.as_view(),
        name="current-search-preferences",
    ),
]
