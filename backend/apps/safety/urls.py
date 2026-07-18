from django.urls import path

from .views import (
    BlockDeleteView,
    BlockListCreateView,
)


app_name = "safety"

urlpatterns = [
    path(
        "blocks/",
        BlockListCreateView.as_view(),
        name="block-list-create",
    ),
    path(
        "blocks/<uuid:block_id>/",
        BlockDeleteView.as_view(),
        name="block-delete",
    ),
]
