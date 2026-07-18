"""
Modèles du module de sécurité communautaire Mbolo.

Ce fichier contient deux modèles principaux :

1. Block
   Permet à un utilisateur d'en bloquer un autre.

2. Report
   Permet à un utilisateur de signaler un autre utilisateur
   pour un comportement potentiellement dangereux, abusif
   ou contraire aux règles de la plateforme.

Les règles critiques sont protégées à plusieurs niveaux :

- validations Django ;
- contraintes PostgreSQL ;
- identifiants UUID ;
- index de performance ;
- limitation de l'exposition des données personnelles ;
- interdiction de l'auto-blocage ;
- interdiction de l'auto-signalement ;
- traçabilité des dates de traitement.
"""

from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Block(models.Model):
    """
    Représente le blocage d'un utilisateur par un autre utilisateur.

    Exemple :

        blocker = utilisateur A
        blocked_user = utilisateur B

    Même si la ligne est directionnelle, les effets fonctionnels
    sont appliqués dans les deux directions :

    - A ne voit plus B ;
    - B ne voit plus A ;
    - A ne peut plus liker B ;
    - B ne peut plus liker A ;
    - le match actif est désactivé ;
    - une future conversation sera interdite.
    """

    # UUID public non séquentiel.
    #
    # Un UUID est beaucoup plus difficile à deviner qu'un identifiant
    # numérique comme 1, 2, 3, etc.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Utilisateur qui déclenche le blocage.
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_blocks",
    )

    # Utilisateur qui est bloqué.
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_blocks",
    )

    # Date de création du blocage.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        """
        Configuration SQL du modèle Block.
        """

        db_table = "safety_block"

        ordering = (
            "-created_at",
        )

        constraints = [
            # Empêche plusieurs lignes de blocage identiques.
            #
            # Exemple interdit :
            #
            # A bloque B
            # A bloque encore B
            models.UniqueConstraint(
                fields=(
                    "blocker",
                    "blocked_user",
                ),
                name="uniq_blocker_blocked_user",
            ),

            # Empêche un utilisateur de se bloquer lui-même.
            models.CheckConstraint(
                condition=~Q(
                    blocker=F("blocked_user")
                ),
                name="block_users_must_differ",
            ),
        ]

        indexes = [
            # Accélère la liste des utilisateurs bloqués
            # par un utilisateur précis.
            models.Index(
                fields=(
                    "blocker",
                    "-created_at",
                ),
                name="block_blocker_created_idx",
            ),

            # Accélère la recherche des utilisateurs ayant bloqué
            # une personne précise.
            models.Index(
                fields=(
                    "blocked_user",
                    "-created_at",
                ),
                name="block_blocked_created_idx",
            ),
        ]

    def __str__(self) -> str:
        """
        Représentation administrative minimale.

        Nous n'affichons volontairement aucune adresse e-mail.
        """

        return f"Block<{self.id}>"

    def clean(self) -> None:
        """
        Refuse explicitement l'auto-blocage.

        La base de données possède déjà une contrainte équivalente,
        mais cette validation produit une erreur métier plus lisible.
        """

        super().clean()

        if (
            self.blocker_id is not None
            and self.blocked_user_id is not None
            and self.blocker_id == self.blocked_user_id
        ):
            raise ValidationError(
                {
                    "blocked_user": (
                        "Un utilisateur ne peut pas "
                        "se bloquer lui-même."
                    )
                }
            )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Valide le modèle avant chaque sauvegarde.

        Cette défense reste active pour les écritures provenant :

        - de l'API ;
        - de l'administration Django ;
        - d'un script interne ;
        - d'une commande manage.py ;
        - d'une future tâche asynchrone.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )


class ReportReason(models.TextChoices):
    """
    Motifs normalisés d'un signalement.

    La première valeur est enregistrée dans PostgreSQL.

    La deuxième valeur est le libellé lisible dans
    l'administration Django.
    """

    HARASSMENT = (
        "harassment",
        "Harcèlement",
    )

    FAKE_PROFILE = (
        "fake_profile",
        "Faux profil ou usurpation",
    )

    SCAM = (
        "scam",
        "Arnaque ou sollicitation financière",
    )

    INAPPROPRIATE_CONTENT = (
        "inappropriate_content",
        "Contenu inapproprié",
    )

    THREAT = (
        "threat",
        "Menace ou violence",
    )

    SPAM = (
        "spam",
        "Spam ou sollicitation abusive",
    )

    UNDERAGE_SUSPICION = (
        "underage_suspicion",
        "Suspicion de personne mineure",
    )

    OTHER = (
        "other",
        "Autre motif",
    )


class ReportStatus(models.TextChoices):
    """
    États possibles du workflow de modération.

    Un utilisateur ordinaire ne pourra pas choisir ou modifier
    directement ce statut depuis l'API publique.
    """

    PENDING = (
        "pending",
        "En attente",
    )

    UNDER_REVIEW = (
        "under_review",
        "En cours d'examen",
    )

    RESOLVED = (
        "resolved",
        "Traité",
    )

    REJECTED = (
        "rejected",
        "Rejeté",
    )


class Report(models.Model):
    """
    Représente un signalement effectué contre un utilisateur.

    Exemple :

        reporter = utilisateur A
        reported_user = utilisateur B
        reason = harassment
        description = comportement observé

    Le signalement n'est pas automatiquement une preuve de faute.

    Il constitue une information à examiner par les personnes
    responsables de la modération.
    """

    # UUID public non séquentiel.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Utilisateur qui dépose le signalement.
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_reports",
    )

    # Utilisateur faisant l'objet du signalement.
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_reports",
    )

    # Motif normalisé.
    #
    # L'utilisation de choices empêche les valeurs libres
    # comme "hack", "admin", "urgent123", etc.
    reason = models.CharField(
        max_length=32,
        choices=ReportReason.choices,
    )

    # Explication facultative fournie par le déclarant.
    #
    # La taille maximale limite :
    #
    # - les abus ;
    # - le spam ;
    # - la consommation excessive de stockage ;
    # - les charges inutiles dans les journaux et interfaces.
    description = models.TextField(
        blank=True,
        default="",
        max_length=2000,
    )

    # État du traitement.
    #
    # Le statut initial est toujours "pending".
    status = models.CharField(
        max_length=24,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        db_index=True,
    )

    # Identifiant du modérateur ayant pris le dossier en charge.
    #
    # SET_NULL conserve le signalement si le compte du modérateur
    # est désactivé ou supprimé plus tard.
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_reports",
        null=True,
        blank=True,
    )

    # Note interne réservée à la modération.
    #
    # Ce champ ne devra jamais être renvoyé par l'API utilisateur.
    moderator_note = models.TextField(
        blank=True,
        default="",
        max_length=4000,
    )

    # Date de création du signalement.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Date de dernière modification.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # Date effective du traitement.
    #
    # Elle sera renseignée lorsque le statut devient :
    #
    # - resolved ;
    # - rejected.
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        """
        Configuration SQL du modèle Report.
        """

        db_table = "safety_report"

        ordering = (
            "-created_at",
        )

        constraints = [
            # Empêche l'auto-signalement.
            models.CheckConstraint(
                condition=~Q(
                    reporter=F("reported_user")
                ),
                name="report_users_must_differ",
            ),
        ]

        indexes = [
            # Accélère la liste des signalements déposés
            # par un utilisateur.
            models.Index(
                fields=(
                    "reporter",
                    "-created_at",
                ),
                name="report_reporter_created_idx",
            ),

            # Accélère les recherches effectuées par la modération
            # sur un utilisateur signalé.
            models.Index(
                fields=(
                    "reported_user",
                    "-created_at",
                ),
                name="report_target_created_idx",
            ),

            # Accélère la file de traitement des signalements.
            models.Index(
                fields=(
                    "status",
                    "-created_at",
                ),
                name="report_status_created_idx",
            ),

            # Accélère les analyses par motif.
            models.Index(
                fields=(
                    "reason",
                    "-created_at",
                ),
                name="report_reason_created_idx",
            ),
        ]

    def __str__(self) -> str:
        """
        Représentation administrative sans donnée personnelle.
        """

        return (
            f"Report<{self.id}:{self.reason}:{self.status}>"
        )

    def clean(self) -> None:
        """
        Applique les validations métier du signalement.
        """

        super().clean()

        # Interdiction de se signaler soi-même.
        if (
            self.reporter_id is not None
            and self.reported_user_id is not None
            and self.reporter_id == self.reported_user_id
        ):
            raise ValidationError(
                {
                    "reported_user": (
                        "Un utilisateur ne peut pas "
                        "se signaler lui-même."
                    )
                }
            )

        # Une note de modération ne doit pas être associée
        # à un dossier sans modérateur.
        if (
            self.moderator_note
            and self.reviewed_by_id is None
        ):
            raise ValidationError(
                {
                    "moderator_note": (
                        "Une note de modération nécessite "
                        "un modérateur responsable."
                    )
                }
            )

        # Un dossier en attente ne doit pas être considéré
        # comme déjà résolu.
        if (
            self.status
            in {
                ReportStatus.PENDING,
                ReportStatus.UNDER_REVIEW,
            }
            and self.resolved_at is not None
        ):
            raise ValidationError(
                {
                    "resolved_at": (
                        "Un signalement non terminé ne peut pas "
                        "avoir de date de résolution."
                    )
                }
            )

        # Un signalement finalisé doit posséder une date de résolution.
        if (
            self.status
            in {
                ReportStatus.RESOLVED,
                ReportStatus.REJECTED,
            }
            and self.resolved_at is None
        ):
            raise ValidationError(
                {
                    "resolved_at": (
                        "Un signalement finalisé doit posséder "
                        "une date de résolution."
                    )
                }
            )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Valide le signalement avant chaque sauvegarde.

        La validation automatique protège également les opérations
        internes qui ne passent pas par l'API REST.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )
