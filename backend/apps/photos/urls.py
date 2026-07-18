"""
Routes API des photos de profil.

Préfixe final :

    /api/v1/profiles/photos/
"""

from django.urls import path

from .views import (
    ProfilePhotoDetailView,
    ProfilePhotoListCreateView,
)


app_name = "photos"


urlpatterns = [
    path(
        "",
        ProfilePhotoListCreateView.as_view(),
        name="photo-list-create",
    ),
    path(
        "<uuid:photo_id>/",
        ProfilePhotoDetailView.as_view(),
        name="photo-detail",
    ),
]
