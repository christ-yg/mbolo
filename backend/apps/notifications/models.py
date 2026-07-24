
"""
Modèle durable du centre de notifications Mbolo.

Une notification appartient toujours à un seul destinataire.
Le frontend ne peut jamais choisir le destinataire ni créer
directement une notification.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Notification(models.Model):
    """
    Événement visible dans le centre de notifications.

    Sécurité et conception :

    - UUID non séquentiel ;
    - destinataire obligatoire ;
    - contenu court et maîtrisé côté serveur ;
    - chemin interne validé ;
    - métadonnées JSON réservées aux données non sensibles ;
    - source_key unique par destinataire pour éviter les doublons ;
    - lecture représentée par read_at.
    """

    class Kind(models.TextChoices):
        MESSAGE = "message", "Message"
        MATCH = "match", "Nouveau match"
        LIKE = "like", "Like"
        SUPER_LIKE = "super_like", "Super Like"
        SECURITY = "security", "Sécurité"
        SYSTEM = "system", "Système"

    MAX_TITLE_LENGTH = 120
    MAX_BODY_LENGTH = 240
    MAX_TARGET_PATH_LENGTH = 500
    MAX_SOURCE_KEY_LENGTH = 160

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    kind = models.CharField(
        max_length=24,
        choices=Kind.choices,
        db_index=True,
    )

    title = models.CharField(
        max_length=MAX_TITLE_LENGTH,
    )

    body = models.CharField(
        max_length=MAX_BODY_LENGTH,
        blank=True,
        default="",
    )

    target_path = models.CharField(
        max_length=MAX_TARGET_PATH_LENGTH,
        blank=True,
        default="",
    )

    source_key = models.CharField(
        max_length=MAX_SOURCE_KEY_LENGTH,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        db_table = "notifications_notification"
        ordering = ("-created_at", "-id")

        constraints = [
            models.UniqueConstraint(
                fields=("recipient", "source_key"),
                name="notification_recipient_source_unique",
            ),
        ]

        indexes = [
            models.Index(
                fields=("recipient", "read_at", "-created_at"),
                name="notif_user_read_created_idx",
            ),
            models.Index(
                fields=("recipient", "kind", "-created_at"),
                name="notif_user_kind_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Notification<{self.id}>"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def clean(self) -> None:
        """
        Valide les données avant sauvegarde.

        target_path doit rester un chemin interne. Une URL absolue
        pourrait créer une redirection ouverte vers un site malveillant.
        """

        super().clean()

        self.title = (self.title or "").strip()
        self.body = (self.body or "").strip()
        self.target_path = (self.target_path or "").strip()
        self.source_key = (self.source_key or "").strip()

        if not self.title:
            raise ValidationError(
                {"title": "Le titre de la notification est obligatoire."}
            )

        if not self.source_key:
            raise ValidationError(
                {"source_key": "La clé de source est obligatoire."}
            )

        if self.target_path and not self.target_path.startswith("/"):
            raise ValidationError(
                {
                    "target_path": (
                        "La destination doit être un chemin interne "
                        "commençant par '/'."
                    )
                }
            )

        if not isinstance(self.metadata, dict):
            raise ValidationError(
                {"metadata": "Les métadonnées doivent être un objet JSON."}
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
