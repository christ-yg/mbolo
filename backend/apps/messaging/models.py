"""
Modèles de la messagerie privée Mbolo.

Une conversation est liée à un match actif.
Un message appartient à une conversation et possède un expéditeur.

Le champ read_at permet de déterminer si le destinataire
a déjà consulté le message.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.interactions.models import Match


class Conversation(models.Model):
    """
    Conversation privée associée à un match.

    Règles principales :

    - un match ne possède qu'une seule conversation ;
    - la conversation est utilisable uniquement si le match est actif ;
    - seuls les deux participants du match peuvent y accéder.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name="conversation",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "messaging_conversation"
        ordering = ("-updated_at",)

        indexes = [
            models.Index(
                fields=("-updated_at",),
                name="conversation_updated_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Conversation<{self.id}>"

    @property
    def is_active(self) -> bool:
        """
        Une conversation est active uniquement si son match est actif.
        """

        return self.match.is_active

    def includes_user(self, user) -> bool:
        """
        Vérifie si le compte appartient au match.
        """

        if not getattr(user, "is_authenticated", False):
            return False

        try:
            profile = user.profile
        except AttributeError:
            return False

        return self.match.includes_profile(profile)

    def other_profile_for_user(self, user):
        """
        Retourne le profil public de l'autre participant.
        """

        if not self.includes_user(user):
            raise ValidationError(
                "Ce compte ne participe pas à cette conversation."
            )

        return self.match.other_profile_for(user.profile)

    def unread_count_for_user(self, user) -> int:
        """
        Compte les messages reçus et non lus par le compte.

        Les propres messages de l'utilisateur ne sont jamais comptés.
        """

        if not self.includes_user(user):
            return 0

        return (
            self.messages
            .exclude(sender=user)
            .filter(read_at__isnull=True)
            .count()
        )

    def clean(self) -> None:
        """
        Vérifie que la conversation possède bien un match.
        """

        super().clean()

        if self.match_id is None:
            raise ValidationError(
                {
                    "match": (
                        "Une conversation doit être liée à un match."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """
        Valide la conversation avant chaque sauvegarde.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )


class Message(models.Model):
    """
    Message texte envoyé dans une conversation privée.

    L'expéditeur est toujours un compte User Django.

    Le frontend ne peut jamais choisir l'identité de l'expéditeur.

    Lecture :

    - read_at = None : message non lu ;
    - read_at contient une date : message lu.
    """

    MAX_BODY_LENGTH = 2000

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_private_messages",
    )

    body = models.TextField(
        max_length=MAX_BODY_LENGTH,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "messaging_message"
        ordering = ("created_at",)

        indexes = [
            models.Index(
                fields=(
                    "conversation",
                    "created_at",
                ),
                name="msg_conv_created_idx",
            ),
            models.Index(
                fields=(
                    "sender",
                    "created_at",
                ),
                name="msg_sender_created_idx",
            ),
            models.Index(
                fields=(
                    "conversation",
                    "read_at",
                ),
                name="msg_conv_read_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Message<{self.id}>"

    @property
    def is_read(self) -> bool:
        """
        Indique si le destinataire a lu le message.
        """

        return self.read_at is not None

    def is_mine_for(self, user) -> bool:
        """
        Indique si le message appartient au compte transmis.
        """

        if not getattr(user, "is_authenticated", False):
            return False

        return self.sender_id == user.id

    def clean(self) -> None:
        """
        Applique les règles de validation et de sécurité.
        """

        super().clean()

        normalized_body = (self.body or "").strip()

        if not normalized_body:
            raise ValidationError(
                {
                    "body": (
                        "Le message ne peut pas être vide."
                    )
                }
            )

        if len(normalized_body) > self.MAX_BODY_LENGTH:
            raise ValidationError(
                {
                    "body": (
                        "Le message dépasse la longueur maximale "
                        f"de {self.MAX_BODY_LENGTH} caractères."
                    )
                }
            )

        self.body = normalized_body

        if (
            self.conversation_id is not None
            and not self.conversation.is_active
        ):
            raise ValidationError(
                {
                    "conversation": (
                        "Cette conversation est inactive."
                    )
                }
            )

        if (
            self.conversation_id is not None
            and self.sender_id is not None
            and not self.conversation.includes_user(
                self.sender
            )
        ):
            raise ValidationError(
                {
                    "sender": (
                        "L'expéditeur ne participe pas "
                        "à cette conversation."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """
        Valide le message avant chaque sauvegarde.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )
