
from django.urls import path

from .views import (
    NotificationDeleteView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
)


app_name = "notifications"


urlpatterns = [
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="list",
    ),
    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="unread-count",
    ),
    path(
        "notifications/read-all/",
        NotificationMarkAllReadView.as_view(),
        name="read-all",
    ),
    path(
        "notifications/<uuid:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="read",
    ),
    path(
        "notifications/<uuid:notification_id>/",
        NotificationDeleteView.as_view(),
        name="delete",
    ),
]
