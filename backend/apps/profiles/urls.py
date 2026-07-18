from django.urls import path

from .views import CurrentProfileView


app_name = "profiles"

urlpatterns = [
    path(
        "me/",
        CurrentProfileView.as_view(),
        name="current-profile",
    ),
]
