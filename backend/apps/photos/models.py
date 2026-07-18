"""
Modèles du module de gestion des photos de profil.

Objectifs de sécurité et de conception :

- identifiants UUID non séquentiels ;
- noms de fichiers générés par le serveur ;
- aucune confiance dans le nom envoyé par le client ;
- six positions maximum par profil ;
- une seule photo principale ;
- contraintes appliquées directement dans PostgreSQL ;
- traçabilité de la création et des modifications.

Le traitement réel des images sera effectué dans un service dédié :

- vérification du contenu réel ;
- contrôle des dimensions ;
- contrôle de la taille ;
- suppression des métadonnées EXIF ;
- réencodage dans un format sûr ;
- génération d'un nouveau fichier.
"""

from uuid import uuid4

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q


def profile_photo_upload_path(
    instance: "ProfilePhoto",
    original_filename: str,
) -> str:
    """
    Génère le chemin de stockage d'une photo.

    Le nom original transmis par l'utilisateur est volontairement ignoré.

    Exemple de chemin produit :

        profiles/<uuid-profil>/<nom-aléatoire>.webp

    Cela protège notamment contre :

    - les traversées de répertoires ;
    - les noms contenant des caractères dangereux ;
    - l'écrasement volontaire d'un fichier ;
    - la divulgation du nom original ;
    - les extensions trompeuses.
    """

    del original_filename

    random_filename = f"{uuid4().hex}.webp"

    return (
        f"profiles/"
        f"{instance.profile_id}/"
        f"{random_filename}"
    )


class ProfilePhoto(models.Model):
    """
    Représente une photo appartenant à un profil Mbolo.

    Les photos sont privées au niveau de leur administration :

    un utilisateur ordinaire ne pourra modifier ou supprimer
    que les photos appartenant à son propre profil.
    """

    # UUID exposable dans les routes API.
    #
    # Contrairement à un entier auto-incrémenté, cet identifiant
    # est difficile à deviner ou à énumérer.
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # Profil propriétaire de la photo.
    #
    # CASCADE signifie que la suppression du profil entraîne
    # la suppression de ses lignes de photos.
    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="photos",
    )

    # Fichier image stocké par Django.
    #
    # Le nom final est produit par profile_photo_upload_path().
    image = models.ImageField(
        upload_to=profile_photo_upload_path,
        max_length=500,
    )

    # Position dans la galerie.
    #
    # Les valeurs autorisées sont :
    #
    # 0, 1, 2, 3, 4 et 5.
    #
    # Cela correspond à six photos maximum par profil.
    position = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5),
        ],
    )

    # Indique la photo utilisée comme image principale.
    #
    # Une contrainte PostgreSQL garantit qu'un profil
    # ne possède jamais deux photos principales simultanément.
    is_primary = models.BooleanField(
        default=False,
    )

    # Date de création de la photo.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Date de dernière modification.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        """
        Configuration SQL du modèle ProfilePhoto.
        """

        db_table = "photos_profile_photo"

        ordering = (
            "position",
            "created_at",
        )

        constraints = [
            # Un profil ne peut pas utiliser deux fois
            # la même position dans sa galerie.
            models.UniqueConstraint(
                fields=(
                    "profile",
                    "position",
                ),
                name="photo_profile_position_uniq",
            ),

            # Un profil ne peut posséder qu'une seule photo principale.
            #
            # condition=Q(is_primary=True) transforme cette contrainte
            # en index unique partiel PostgreSQL.
            models.UniqueConstraint(
                fields=(
                    "profile",
                ),
                condition=Q(
                    is_primary=True,
                ),
                name="photo_one_primary_profile",
            ),
        ]

        indexes = [
            # Accélère le chargement ordonné de la galerie.
            models.Index(
                fields=(
                    "profile",
                    "position",
                ),
                name="photo_profile_position_idx",
            ),

            # Accélère la récupération de la photo principale.
            models.Index(
                fields=(
                    "profile",
                    "is_primary",
                ),
                name="photo_profile_primary_idx",
            ),

            # Accélère les opérations de nettoyage chronologique.
            models.Index(
                fields=(
                    "profile",
                    "-created_at",
                ),
                name="photo_profile_created_idx",
            ),
        ]

    def __str__(self) -> str:
        """
        Représentation administrative sans donnée personnelle.
        """

        return (
            f"ProfilePhoto<"
            f"{self.id}:"
            f"position={self.position}:"
            f"primary={self.is_primary}"
            f">"
        )

    def save(
        self,
        *args,
        **kwargs,
    ) -> None:
        """
        Exécute les validations Django avant la sauvegarde.

        Cette validation protège également les créations provenant :

        - de l'administration Django ;
        - d'un script interne ;
        - d'une commande manage.py ;
        - d'une future tâche asynchrone.

        Les contraintes PostgreSQL restent la dernière ligne de défense.
        """

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )
