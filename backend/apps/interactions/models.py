"""
Modèles de données du module interactions.

Ce fichier définit deux objets principaux :

1. Interaction
   Une décision prise par un utilisateur envers un profil :
   - like ;
   - pass.

2. Match
   Une relation créée lorsque deux utilisateurs se likent
   réciproquement.

Les règles importantes sont protégées à plusieurs niveaux :

- validation Django ;
- contraintes PostgreSQL ;
- index de performance ;
- identifiants UUID ;
- interdiction de s'auto-liker ;
- prévention des doublons.
"""

from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class InteractionDecision(models.TextChoices):
    """
    Liste des décisions autorisées.

    La première valeur est enregistrée dans PostgreSQL.
    La deuxième valeur est le libellé lisible par un humain.

    Exemple :

        "like" est enregistré en base ;
        "J'aime" peut être affiché dans l'administration.
    """

    LIKE = "like", "J'aime"
    PASS = "pass", "Passer"


class Interaction(models.Model):
    """
    Représente une action d'un utilisateur envers un profil.

    Exemple :

        actor = Christ
        target_profile = profil de Marie
        decision = like

    Un utilisateur ne peut conserver qu'une seule interaction
    envers un même profil.

    S'il passe d'un PASS à un LIKE, la ligne existante sera
    mise à jour par le service métier au lieu de créer un doublon.
    """

    # UUID public et non séquentiel.
    #
    # Contrairement aux identifiants 1, 2, 3, etc., un UUID est
    # beaucoup plus difficile à deviner dans une URL ou une API.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Utilisateur qui effectue l'action.
    #
    # Nous utilisons AUTH_USER_MODEL afin de respecter le modèle
    # User personnalisé configuré dans settings.py.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_interactions",
    )

    # Profil qui reçoit le like ou le pass.
    #
    # La chaîne "profiles.Profile" évite certains problèmes
    # d'import circulaire entre les applications Django.
    target_profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="received_interactions",
    )

    # Décision limitée aux valeurs définies dans
    # InteractionDecision : like ou pass.
    decision = models.CharField(
        max_length=16,
        choices=InteractionDecision.choices,
    )

    # Marqueur spécial d'un intérêt Premium.
    #
    # Il reste séparé de ``decision`` : un Super Like est toujours un LIKE
    # pour la création d'un match, mais possède une présentation et un quota
    # spécifiques. Un PASS ne peut jamais conserver ce marqueur.
    is_super_like = models.BooleanField(default=False, db_index=True)

    # Date de création initiale de l'interaction.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Date de dernière modification.
    #
    # Elle change notamment lorsqu'un utilisateur transforme
    # un PASS en LIKE ou inversement.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        """
        Configuration SQL du modèle Interaction.
        """

        # Nom explicite de la table PostgreSQL.
        db_table = "interactions_interaction"

        # Les interactions les plus récemment modifiées
        # apparaissent en premier.
        ordering = (
            "-updated_at",
            "-created_at",
        )

        constraints = [
            # Un utilisateur ne peut avoir qu'une seule interaction
            # envers un profil donné.
            #
            # PostgreSQL appliquera cette règle même si une erreur
            # future apparaît dans l'API ou dans un script.
            models.UniqueConstraint(
                fields=(
                    "actor",
                    "target_profile",
                ),
                name="uniq_actor_target_inter",
            ),
        ]

        indexes = [
            # Optimise les requêtes telles que :
            #
            # "Récupérer tous les likes envoyés par cet utilisateur."
            #
            # Le nom reste inférieur à 30 caractères afin d'éviter
            # l'erreur Django models.E034.
            models.Index(
                fields=(
                    "actor",
                    "decision",
                    "-updated_at",
                ),
                name="inter_actor_decision_idx",
            ),

            # Optimise la recherche d'un like réciproque.
            #
            # Exemple :
            # rechercher si le propriétaire du profil ciblé
            # a déjà liké le profil de l'utilisateur courant.
            models.Index(
                fields=(
                    "target_profile",
                    "decision",
                ),
                name="inter_target_decision_idx",
            ),
        ]

    def __str__(self) -> str:
        """
        Représentation lisible dans l'administration Django.

        Nous n'affichons volontairement aucune adresse e-mail
        afin de limiter l'exposition des données personnelles.
        """

        return f"Interaction<{self.id}:{self.decision}>"

    def clean(self) -> None:
        """
        Applique les règles métier avant la sauvegarde.

        Cette validation empêche un utilisateur de liker
        ou de passer son propre profil.

        Une contrainte SQL simple ne peut pas comparer directement :

            actor.id

        avec :

            target_profile.user.id

        car ces valeurs appartiennent à plusieurs tables.
        La vérification est donc effectuée dans Django.
        """

        super().clean()

        if self.is_super_like and self.decision != InteractionDecision.LIKE:
            raise ValidationError(
                {"is_super_like": "Un Super Like doit être un like positif."}
            )

        # Nous vérifions d'abord que les deux relations existent.
        if (
            self.actor_id is not None
            and self.target_profile_id is not None
        ):
            if self.target_profile.user_id == self.actor_id:
                raise ValidationError(
                    {
                        "target_profile": (
                            "Un utilisateur ne peut pas interagir "
                            "avec son propre profil."
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

        full_clean() applique :

        - la validation des champs ;
        - la validation des choix ;
        - la méthode clean() ;
        - les contraintes de modèle vérifiables par Django.

        Cette protection reste active lorsque les données viennent :

        - de l'administration Django ;
        - d'un script Python ;
        - d'une tâche asynchrone ;
        - d'une commande manage.py.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )


class Match(models.Model):
    """
    Représente un match entre deux profils.

    Un match est créé lorsque deux utilisateurs se likent
    réciproquement.

    Les profils sont stockés dans un ordre canonique :

        profile_one.id < profile_two.id

    Ainsi, la paire A/B et la paire B/A sont considérées
    comme la même relation.
    """

    # Identifiant UUID du match.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Premier profil de la paire canonique.
    profile_one = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="matches_as_profile_one",
    )

    # Deuxième profil de la paire canonique.
    profile_two = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="matches_as_profile_two",
    )

    # Permet de désactiver un match sans nécessairement
    # supprimer immédiatement son historique.
    is_active = models.BooleanField(
        default=True,
    )

    # Date de création du match.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Date de dernière modification du match.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        """
        Configuration SQL du modèle Match.
        """

        db_table = "interactions_match"

        # Les matchs les plus récents apparaissent en premier.
        ordering = (
            "-created_at",
        )

        constraints = [
            # Une paire de profils ne peut produire
            # qu'un seul match.
            models.UniqueConstraint(
                fields=(
                    "profile_one",
                    "profile_two",
                ),
                name="uniq_profile_pair_match",
            ),

            # La base interdit un match d'un profil avec lui-même.
            #
            # Exemple interdit :
            #
            # profile_one = profil A
            # profile_two = profil A
            models.CheckConstraint(
                condition=~Q(
                    profile_one=F("profile_two")
                ),
                name="match_profiles_different",
            ),
        ]

        indexes = [
            # Optimise la recherche des matchs actifs lorsque
            # le profil est enregistré dans profile_one.
            models.Index(
                fields=(
                    "profile_one",
                    "is_active",
                    "-created_at",
                ),
                name="match_prof1_active_idx",
            ),

            # Optimise la recherche des matchs actifs lorsque
            # le profil est enregistré dans profile_two.
            models.Index(
                fields=(
                    "profile_two",
                    "is_active",
                    "-created_at",
                ),
                name="match_prof2_active_idx",
            ),
        ]

    def __str__(self) -> str:
        """
        Représentation administrative minimale.

        Nous n'affichons ni nom, ni e-mail des participants.
        """

        return f"Match<{self.id}>"

    def clean(self) -> None:
        """
        Vérifie la cohérence des deux profils.

        Deux contrôles sont réalisés :

        1. les profils doivent être différents ;
        2. ils doivent respecter l'ordre canonique.
        """

        super().clean()

        if (
            self.profile_one_id is not None
            and self.profile_two_id is not None
        ):
            # Interdiction du match avec soi-même.
            if self.profile_one_id == self.profile_two_id:
                raise ValidationError(
                    {
                        "profile_two": (
                            "Un profil ne peut pas être matché "
                            "avec lui-même."
                        )
                    }
                )

            # Les UUID sont comparés sous forme de chaînes
            # afin d'obtenir un ordre stable et déterministe.
            if str(self.profile_one_id) > str(
                self.profile_two_id
            ):
                raise ValidationError(
                    {
                        "profile_one": (
                            "Les profils du match ne respectent pas "
                            "l'ordre canonique."
                        )
                    }
                )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Valide systématiquement le match avant sauvegarde.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )

    def includes_profile(
        self,
        profile,
    ) -> bool:
        """
        Indique si un profil appartient au match.

        Exemple :

            match.includes_profile(mon_profil)

        retourne True si mon_profil est profile_one
        ou profile_two.
        """

        return profile.id in {
            self.profile_one_id,
            self.profile_two_id,
        }

    def other_profile_for(
        self,
        profile,
    ):
        """
        Retourne l'autre participant du match.

        Exemple :

            si profile correspond à profile_one,
            la méthode retourne profile_two.

        Une ValidationError est déclenchée si le profil transmis
        n'appartient pas au match.
        """

        if profile.id == self.profile_one_id:
            return self.profile_two

        if profile.id == self.profile_two_id:
            return self.profile_one

        raise ValidationError(
            "Ce profil n'appartient pas au match."
        )
