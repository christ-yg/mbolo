"""
Services métier du module Photos.

Cette couche centralise toutes les opérations sensibles liées aux photos :

- vérification de l'éligibilité du compte ;
- traitement sécurisé du fichier ;
- contrôle du nombre maximal de photos ;
- gestion des positions ;
- protection contre les IDOR ;
- garantie d'une seule photo principale ;
- suppression cohérente des fichiers et des lignes PostgreSQL.

Les opérations de création, modification et suppression sont transactionnelles.
"""

from dataclasses import dataclass
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.profiles.models import Profile

from .image_processing import (
    ProcessedImage,
    process_profile_photo,
)
from .models import ProfilePhoto


@dataclass(frozen=True)
class PhotoCreationResult:
    """
    Résultat immuable d'une création de photo.

    photo
        Ligne ProfilePhoto créée dans PostgreSQL.

    processed_width / processed_height
        Dimensions finales après traitement et réencodage.
    """

    photo: ProfilePhoto
    processed_width: int
    processed_height: int


def get_eligible_profile(
    *,
    user,
    lock: bool = False,
) -> Profile:
    """
    Retourne le profil d'un utilisateur autorisé à gérer ses photos.

    Conditions de sécurité :

    - session authentifiée ;
    - compte actif ;
    - compte non suspendu ;
    - adresse e-mail vérifiée ;
    - profil déjà créé.

    Le paramètre lock active SELECT ... FOR UPDATE lorsque l'appel
    intervient dans une transaction d'écriture.
    """

    if not user.is_authenticated:
        raise ValidationError(
            "Une authentification est requise."
        )

    if not user.is_active:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if user.is_suspended:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    if not user.is_email_verified:
        raise ValidationError(
            "L'adresse e-mail doit être vérifiée."
        )

    queryset = Profile.objects

    if lock:
        queryset = queryset.select_for_update()

    try:
        return queryset.get(
            user=user,
        )
    except Profile.DoesNotExist as exc:
        raise ValidationError(
            "Créez votre profil avant d'ajouter des photos."
        ) from exc


def get_next_available_position(
    *,
    profile: Profile,
) -> int:
    """
    Retourne la première position libre de la galerie.

    Les positions autorisées vont de 0 à :

        PROFILE_PHOTO_MAX_COUNT - 1

    Avec la configuration actuelle, cela correspond à 0–5.
    """

    maximum_count = int(
        settings.PROFILE_PHOTO_MAX_COUNT
    )

    used_positions = set(
        ProfilePhoto.objects.filter(
            profile=profile,
        ).values_list(
            "position",
            flat=True,
        )
    )

    for position in range(maximum_count):
        if position not in used_positions:
            return position

    raise ValidationError(
        {
            "image": (
                "Le nombre maximal de photos est atteint."
            )
        }
    )


def validate_position_available(
    *,
    profile: Profile,
    position: int,
    excluded_photo_id: UUID | None = None,
) -> None:
    """
    Vérifie qu'une position de galerie n'est pas déjà utilisée.

    excluded_photo_id permet à une photo de conserver sa propre position
    pendant une modification.
    """

    maximum_count = int(
        settings.PROFILE_PHOTO_MAX_COUNT
    )

    if position < 0 or position >= maximum_count:
        raise ValidationError(
            {
                "position": (
                    f"La position doit être comprise entre 0 et "
                    f"{maximum_count - 1}."
                )
            }
        )

    queryset = ProfilePhoto.objects.filter(
        profile=profile,
        position=position,
    )

    if excluded_photo_id is not None:
        queryset = queryset.exclude(
            id=excluded_photo_id,
        )

    if queryset.exists():
        raise ValidationError(
            {
                "position": (
                    "Cette position est déjà occupée."
                )
            }
        )


def remove_other_primary_flags(
    *,
    profile: Profile,
    excluded_photo_id: UUID | None = None,
) -> None:
    """
    Retire le statut principal aux autres photos.

    queryset.update() est intentionnel ici :

    - une seule requête SQL est nécessaire ;
    - les lignes sont déjà protégées par la transaction ;
    - aucun fichier n'est modifié ;
    - aucune validation de fichier n'est requise.
    """

    queryset = ProfilePhoto.objects.filter(
        profile=profile,
        is_primary=True,
    )

    if excluded_photo_id is not None:
        queryset = queryset.exclude(
            id=excluded_photo_id,
        )

    queryset.update(
        is_primary=False,
    )


@transaction.atomic
def create_profile_photo(
    *,
    user,
    uploaded_file,
    position: int | None = None,
    is_primary: bool = False,
) -> PhotoCreationResult:
    """
    Traite puis crée une photo de profil.

    Déroulement :

    1. verrouillage du profil ;
    2. verrouillage des photos existantes ;
    3. vérification de la limite ;
    4. sélection de la position ;
    5. traitement sécurisé du fichier ;
    6. gestion de la photo principale ;
    7. création de la ligne PostgreSQL.

    Si l'enregistrement SQL échoue après création du fichier,
    le fichier est immédiatement supprimé.
    """

    profile = get_eligible_profile(
        user=user,
        lock=True,
    )

    existing_photos = (
        ProfilePhoto.objects
        .select_for_update()
        .filter(
            profile=profile,
        )
    )

    photo_count = existing_photos.count()

    maximum_count = int(
        settings.PROFILE_PHOTO_MAX_COUNT
    )

    if photo_count >= maximum_count:
        raise ValidationError(
            {
                "image": (
                    f"Un profil ne peut pas posséder plus de "
                    f"{maximum_count} photos."
                )
            }
        )

    if position is None:
        selected_position = get_next_available_position(
            profile=profile,
        )
    else:
        selected_position = position

    validate_position_available(
        profile=profile,
        position=selected_position,
    )

    # La toute première photo doit obligatoirement devenir principale.
    should_be_primary = (
        is_primary
        or photo_count == 0
    )

    processed_image: ProcessedImage = (
        process_profile_photo(
            uploaded_file
        )
    )

    if should_be_primary:
        remove_other_primary_flags(
            profile=profile,
        )

    photo = ProfilePhoto(
        profile=profile,
        position=selected_position,
        is_primary=should_be_primary,
    )

    # save=False demande à Django d'enregistrer le fichier dans le stockage,
    # sans encore créer la ligne ProfilePhoto.
    photo.image.save(
        processed_image.filename,
        processed_image.content,
        save=False,
    )

    try:
        photo.save()
    except Exception:
        # Compensation : évite un fichier orphelin si PostgreSQL
        # rejette ensuite la ligne.
        if photo.image and photo.image.name:
            photo.image.storage.delete(
                photo.image.name
            )

        raise

    return PhotoCreationResult(
        photo=photo,
        processed_width=processed_image.width,
        processed_height=processed_image.height,
    )


def get_owned_photo(
    *,
    user,
    photo_id: UUID,
    lock: bool = False,
) -> ProfilePhoto:
    """
    Retourne une photo uniquement si elle appartient à l'utilisateur.

    La propriété est vérifiée directement dans la requête SQL :

        id = photo_id
        ET profile.user = utilisateur connecté

    Cette approche protège contre les IDOR.
    """

    queryset = (
        ProfilePhoto.objects
        .select_related(
            "profile",
            "profile__user",
        )
    )

    if lock:
        queryset = queryset.select_for_update()

    try:
        return queryset.get(
            id=photo_id,
            profile__user=user,
        )
    except ProfilePhoto.DoesNotExist as exc:
        # Message volontairement générique :
        # il ne révèle pas si la photo existe chez un autre utilisateur.
        raise ValidationError(
            "La photo demandée n'est pas disponible."
        ) from exc


@transaction.atomic
def update_profile_photo(
    *,
    user,
    photo_id: UUID,
    position: int | None = None,
    is_primary: bool | None = None,
) -> ProfilePhoto:
    """
    Modifie la position ou le statut principal d'une photo.

    Règles :

    - seule une photo appartenant au compte peut être modifiée ;
    - une position ne peut être occupée que par une photo ;
    - une galerie non vide conserve toujours une photo principale ;
    - PostgreSQL garantit qu'il n'existe jamais deux photos principales.
    """

    photo = get_owned_photo(
        user=user,
        photo_id=photo_id,
        lock=True,
    )

    profile = (
        Profile.objects
        .select_for_update()
        .get(
            id=photo.profile_id,
        )
    )

    # Verrouillage de toutes les photos du profil.
    #
    # Cette matérialisation est utile contre deux modifications
    # concurrentes de la photo principale.
    list(
        ProfilePhoto.objects
        .select_for_update()
        .filter(
            profile=profile,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    fields_to_update: list[str] = []

    # ---------------------------------------------------------
    # Modification de la position
    # ---------------------------------------------------------
    if position is not None:
        validate_position_available(
            profile=profile,
            position=position,
            excluded_photo_id=photo.id,
        )

        if photo.position != position:
            photo.position = position

            fields_to_update.append(
                "position"
            )

    # ---------------------------------------------------------
    # Promotion en photo principale
    # ---------------------------------------------------------
    if is_primary is True and not photo.is_primary:
        # L'ancienne photo principale doit être rétrogradée avant
        # que la nouvelle soit sauvegardée.
        remove_other_primary_flags(
            profile=profile,
            excluded_photo_id=photo.id,
        )

        photo.is_primary = True

        fields_to_update.append(
            "is_primary"
        )

    # ---------------------------------------------------------
    # Retrait du statut principal
    # ---------------------------------------------------------
    elif is_primary is False and photo.is_primary:
        replacement = (
            ProfilePhoto.objects
            .select_for_update()
            .filter(
                profile=profile,
            )
            .exclude(
                id=photo.id,
            )
            .order_by(
                "position",
                "created_at",
            )
            .first()
        )

        if replacement is None:
            raise ValidationError(
                {
                    "is_primary": (
                        "La seule photo du profil doit rester "
                        "principale."
                    )
                }
            )

        # IMPORTANT :
        #
        # On rétrograde d'abord la photo actuelle.
        # Cela libère la contrainte unique partielle PostgreSQL.
        photo.is_primary = False

        if "is_primary" not in fields_to_update:
            fields_to_update.append(
                "is_primary"
            )

        if "updated_at" not in fields_to_update:
            fields_to_update.append(
                "updated_at"
            )

        photo.save(
            update_fields=fields_to_update,
        )

        # La promotion de la remplaçante intervient ensuite,
        # dans la même transaction atomique.
        replacement.is_primary = True

        replacement.save(
            update_fields=[
                "is_primary",
                "updated_at",
            ]
        )

        # La photo courante a déjà été sauvegardée.
        return photo

    if fields_to_update:
        fields_to_update.append(
            "updated_at"
        )

        photo.save(
            update_fields=fields_to_update,
        )

    return photo


@transaction.atomic
def delete_profile_photo(
    *,
    user,
    photo_id: UUID,
) -> None:
    """
    Supprime une photo appartenant au compte connecté.

    Si la photo supprimée était principale, la première photo restante
    devient automatiquement principale.

    Le signal post_delete se charge ensuite de supprimer le fichier
    physique après validation de la transaction.
    """

    photo = get_owned_photo(
        user=user,
        photo_id=photo_id,
        lock=True,
    )

    profile_id = photo.profile_id

    was_primary = photo.is_primary

    # Verrouille également les autres photos avant réattribution.
    list(
        ProfilePhoto.objects
        .select_for_update()
        .filter(
            profile_id=profile_id,
        )
        .values_list(
            "id",
            flat=True,
        )
    )

    photo.delete()

    if not was_primary:
        return

    replacement = (
        ProfilePhoto.objects
        .select_for_update()
        .filter(
            profile_id=profile_id,
        )
        .order_by(
            "position",
            "created_at",
        )
        .first()
    )

    if replacement is not None:
        replacement.is_primary = True

        replacement.save(
            update_fields=[
                "is_primary",
                "updated_at",
            ]
        )
