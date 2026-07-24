"""
Stockage privé des justificatifs de vérification.

Ce stockage est volontairement séparé de MEDIA_ROOT. Même en développement,
une URL /media/... ne peut donc pas rendre un selfie de vérification public.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateVerificationStorage(FileSystemStorage):
    """Stockage local sans URL publique pour les justificatifs sensibles."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "location",
            settings.PRIVATE_VERIFICATION_MEDIA_ROOT,
        )
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)

