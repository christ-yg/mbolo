from django.contrib.sessions.models import Session
from django.utils import timezone

from .models import User


def revoke_other_sessions(
    *,
    user: User,
    current_session_key: str | None,
) -> int:
    """
    Supprime les sessions Django appartenant au compte, sauf la session
    courante. Les sessions expirées sont ignorées.
    """
    revoked = 0
    sessions = Session.objects.filter(
        expire_date__gte=timezone.now(),
    )

    for session in sessions.iterator():
        if session.session_key == current_session_key:
            continue

        try:
            session_user_id = session.get_decoded().get(
                "_auth_user_id"
            )
        except Exception:
            continue

        if str(session_user_id) != str(user.pk):
            continue

        session.delete()
        revoked += 1

    return revoked
