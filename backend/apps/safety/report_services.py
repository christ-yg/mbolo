"""
Services métier des signalements utilisateurs.

La logique métier est séparée des vues HTTP afin de pouvoir être
réutilisée ultérieurement par :

- le frontend web ;
- l'application mobile ;
- une interface interne ;
- une commande Django ;
- une tâche asynchrone ;
- un outil de modération.

Les opérations utilisent une transaction PostgreSQL atomique.
"""

from dataclasses import dataclass
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    Report,
    ReportReason,
    ReportStatus,
)


User = get_user_model()


@dataclass(frozen=True)
class ReportCreationResult:
    """
    Résultat immuable de la création d'un signalement.
    """

    report: Report


def validate_reporter(
    *,
    reporter,
) -> None:
    """
    Vérifie que le déclarant est autorisé à signaler un utilisateur.

    Conditions :

    - session authentifiée ;
    - compte actif ;
    - compte non suspendu ;
    - adresse e-mail vérifiée.
    """

    if not reporter.is_authenticated:
        raise ValidationError(
            "Une authentification est requise."
        )

    if not reporter.is_active:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if reporter.is_suspended:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if not reporter.is_email_verified:
        raise ValidationError(
            "L'adresse e-mail doit être vérifiée."
        )


def get_report_target(
    *,
    reporter,
    reported_user_id: UUID,
):
    """
    Récupère la personne signalée.

    Le message d'erreur reste générique lorsque le compte n'existe pas,
    afin de limiter l'énumération des comptes.
    """

    try:
        reported_user = (
            User.objects
            .select_for_update()
            .get(
                id=reported_user_id,
            )
        )
    except User.DoesNotExist as exc:
        raise ValidationError(
            "L'utilisateur demandé n'est pas disponible."
        ) from exc

    if reported_user.id == reporter.id:
        raise ValidationError(
            "Vous ne pouvez pas vous signaler vous-même."
        )

    return reported_user


def validate_report_content(
    *,
    reason: str,
    description: str,
) -> str:
    """
    Défense supplémentaire pour les appels directs au service.

    Le sérialiseur valide déjà les données HTTP, mais ce service
    pourrait être appelé plus tard depuis une tâche interne.
    """

    valid_reasons = {
        choice.value
        for choice in ReportReason
    }

    if reason not in valid_reasons:
        raise ValidationError(
            {
                "reason": (
                    "Le motif du signalement est invalide."
                )
            }
        )

    normalized_description = " ".join(
        description.split()
    )

    if len(normalized_description) > 2000:
        raise ValidationError(
            {
                "description": (
                    "La description ne peut pas dépasser "
                    "2000 caractères."
                )
            }
        )

    if (
        reason == ReportReason.OTHER
        and not normalized_description
    ):
        raise ValidationError(
            {
                "description": (
                    "Une description est obligatoire "
                    "pour le motif 'other'."
                )
            }
        )

    return normalized_description


@transaction.atomic
def create_report(
    *,
    reporter,
    reported_user_id: UUID,
    reason: str,
    description: str = "",
) -> ReportCreationResult:
    """
    Crée un signalement dans une transaction atomique.

    Les champs de modération sont imposés côté serveur :

    - status = pending ;
    - reviewed_by = None ;
    - moderator_note = chaîne vide ;
    - resolved_at = None.

    Le frontend ne peut donc pas marquer lui-même un dossier
    comme traité ou rejeté.
    """

    validate_reporter(
        reporter=reporter,
    )

    reported_user = get_report_target(
        reporter=reporter,
        reported_user_id=reported_user_id,
    )

    normalized_description = (
        validate_report_content(
            reason=reason,
            description=description,
        )
    )

    report = Report.objects.create(
        reporter=reporter,
        reported_user=reported_user,
        reason=reason,
        description=normalized_description,

        # Valeurs contrôlées exclusivement par le backend.
        status=ReportStatus.PENDING,
        reviewed_by=None,
        moderator_note="",
        resolved_at=None,
    )

    return ReportCreationResult(
        report=report,
    )
