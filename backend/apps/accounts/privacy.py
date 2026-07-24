from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.forms.models import model_to_dict
from django.db.models import Q
from django.utils import timezone

from apps.interactions.models import Interaction, Match
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification
from apps.photos.models import ProfilePhoto
from apps.profiles.models import ProfileVerification
from apps.safety.models import Block, Report

from .models import User


def _json_safe(value):
    """Convertit les types Django en valeurs JSON sans secret technique."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "name"):
        return str(value.name)
    return value


def _model_data(instance, *, exclude=()):
    return _json_safe(
        model_to_dict(instance, exclude=tuple(exclude))
    )


def build_personal_data_export(user: User) -> dict:
    """
    Produit un export portable. Les hashes, cookies, jetons, IP,
    secrets et notes internes de modération sont volontairement exclus.
    """
    try:
        profile = user.profile
    except Exception:
        profile = None

    try:
        preferences = user.search_preferences
    except Exception:
        preferences = None

    photos = (
        ProfilePhoto.objects.filter(profile__user=user)
        .order_by("position")
    )
    interactions = Interaction.objects.filter(actor=user).order_by(
        "created_at"
    )
    matches = Match.objects.filter(
        Q(profile_one__user=user) | Q(profile_two__user=user)
    ).distinct().order_by("created_at")
    conversations = Conversation.objects.filter(
        Q(match__profile_one__user=user)
        | Q(match__profile_two__user=user)
    ).distinct().order_by("created_at")
    sent_messages = Message.objects.filter(sender=user).order_by(
        "created_at"
    )
    notifications = Notification.objects.filter(recipient=user).order_by(
        "created_at"
    )
    blocks = Block.objects.filter(blocker=user).order_by("created_at")
    reports = Report.objects.filter(reporter=user).order_by("created_at")
    verification = (
        ProfileVerification.objects
        .filter(profile__user=user)
        .first()
    )

    return {
        "export": {
            "service": "Mbolo",
            "format_version": 1,
            "generated_at": timezone.now().isoformat(),
            "scope": (
                "Données liées au compte demandeur. Les secrets "
                "d'authentification et données de tiers sont exclus."
            ),
        },
        "account": {
            "id": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        "profile": (
            _model_data(profile, exclude=("user",))
            if profile is not None
            else None
        ),
        "profile_verification": (
            _model_data(
                verification,
                exclude=("profile", "selfie"),
            )
            if verification is not None
            else None
        ),
        "search_preferences": (
            _model_data(preferences, exclude=("user",))
            if preferences is not None
            else None
        ),
        "photos": [
            _model_data(photo, exclude=("profile",))
            for photo in photos
        ],
        "interactions_sent": [
            _model_data(item, exclude=("actor",))
            for item in interactions
        ],
        "matches": [_model_data(item) for item in matches],
        "conversations": [
            _model_data(item) for item in conversations
        ],
        "messages_sent": [
            _model_data(item, exclude=("sender",))
            for item in sent_messages
        ],
        "notifications": [
            _model_data(item, exclude=("recipient", "source_key"))
            for item in notifications
        ],
        "blocks_created": [
            _model_data(item, exclude=("blocker",))
            for item in blocks
        ],
        "reports_submitted": [
            _model_data(
                item,
                exclude=("reporter", "reviewed_by", "moderator_note"),
            )
            for item in reports
        ],
    }


def permanently_delete_account(user: User) -> None:
    """Supprime d'abord les fichiers physiques, puis les lignes en cascade."""
    photos = list(
        ProfilePhoto.objects.filter(profile__user=user)
    )
    for photo in photos:
        if photo.image:
            photo.image.delete(save=False)
    verification = (
        ProfileVerification.objects
        .filter(profile__user=user)
        .first()
    )
    if verification is not None and verification.selfie:
        verification.selfie.delete(save=False)
    user.delete()
