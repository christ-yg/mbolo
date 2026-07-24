from django.urls import path

from .views import (
    InteractionCreateView,
    SuperLikeStateView,
    InteractionRewindView,
    MatchDeactivateView,
    MatchListView,
    ReceivedLikeListView,
    ReceivedLikeRespondView,
)


app_name = "interactions"

urlpatterns = [
    path(
        "super-like/",
        SuperLikeStateView.as_view(),
        name="super-like-state",
    ),
    path(
        "interactions/",
        InteractionCreateView.as_view(),
        name="interaction-create",
    ),
    path(
        "interactions/rewind/",
        InteractionRewindView.as_view(),
        name="interaction-rewind",
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
