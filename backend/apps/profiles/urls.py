from django.urls import path

from .views import (
    CurrentProfileView,
    CurrentSearchPreferencesView,
    DiscoveryProfileListView,
    PublicProfileDetailView,
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
    path(
        "public/<uuid:profile_id>/",
        PublicProfileDetailView.as_view(),
        name="public-profile-detail",
    ),
    path(
        "discovery/",
        DiscoveryProfileListView.as_view(),
        name="discovery",
    ),
]
