from django.urls import path

from .views import (
    InteractionCreateView,
    MatchDeactivateView,
    MatchListView,
    ReceivedLikeListView,
    ReceivedLikeRespondView,
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
    path(
        "matches/<uuid:match_id>/",
        MatchDeactivateView.as_view(),
        name="match-deactivate",
    ),
    path(
        "likes-received/",
        ReceivedLikeListView.as_view(),
        name="received-like-list",
    ),
    path(
        "likes-received/<uuid:interaction_id>/respond/",
        ReceivedLikeRespondView.as_view(),
        name="received-like-respond",
    ),
]
