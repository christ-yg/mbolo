from django.urls import path

from .views import (
    InteractionCreateView,
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
