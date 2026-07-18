from django.urls import path

from .views import (
    InteractionCreateView,
    MatchListView,
)


app_name = "interactions"

urlpatterns = [
    path(
        "interactions/",
        InteractionCreateView.as_view(),
        name="interaction-create",
    ),
    path(
        "matches/",
        MatchListView.as_view(),
        name="match-list",
    ),
]
