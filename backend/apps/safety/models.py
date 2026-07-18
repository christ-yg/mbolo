"""
Modèles du module de sécurité communautaire.

Cette première version contient le modèle Block.

Un blocage est une relation directionnelle :

    blocker      = utilisateur qui déclenche le blocage
    blocked_user = utilisateur qui est bloqué

Même si la ligne est directionnelle, les effets applicatifs du blocage
seront bidirectionnels :

- aucune découverte mutuelle ;
- aucune interaction mutuelle ;
- aucun nouveau match ;
- aucune future conversation.
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

        blocker = Christ
        blocked_user = utilisateur B

    Une seule ligne peut exister pour la même paire directionnelle.
    """

    # UUID non séquentiel exposable dans l'API.
    #
    # Il est beaucoup plus difficile à deviner qu'un identifiant
    # numérique comme 1, 2, 3, etc.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Utilisateur qui effectue le blocage.
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_blocks",
    )

    # Utilisateur qui devient bloqué.
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
            # Un utilisateur ne peut pas créer plusieurs lignes
            # identiques pour la même personne.
            #
            # La contrainte est appliquée directement par PostgreSQL.
            models.UniqueConstraint(
                fields=(
                    "blocker",
                    "blocked_user",
                ),
                name="uniq_blocker_blocked_user",
            ),

            # Interdit :
            #
            # blocker = utilisateur A
            # blocked_user = utilisateur A
            models.CheckConstraint(
                condition=~Q(
                    blocker=F("blocked_user")
                ),
                name="block_users_must_differ",
            ),
        ]

        indexes = [
            # Accélère la récupération de la liste des utilisateurs
            # bloqués par une personne.
            models.Index(
                fields=(
                    "blocker",
                    "-created_at",
                ),
                name="block_blocker_created_idx",
            ),

            # Accélère la recherche des utilisateurs ayant bloqué
            # une personne donnée.
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
        Représentation administrative sans adresse e-mail.
        """

        return f"Block<{self.id}>"

    def clean(self) -> None:
        """
        Refuse explicitement l'auto-blocage.

        La base possède déjà une CheckConstraint, mais cette validation
        permet d'obtenir une erreur métier plus claire avant l'INSERT.
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
                        "Un utilisateur ne peut pas se bloquer lui-même."
                    )
                }
            )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Exécute les validations avant chaque sauvegarde.

        Cette défense reste active pour les créations effectuées depuis :

        - l'API ;
        - l'administration Django ;
        - un script interne ;
        - une tâche asynchrone ;
        - une commande manage.py.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )
