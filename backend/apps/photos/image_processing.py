"""
Traitement sécurisé des photos téléversées sur Mbolo.

Le fichier fourni par le client n'est jamais stocké directement.

Pipeline appliqué :

1. contrôle de la taille ;
2. ouverture avec Pillow ;
3. vérification du contenu réel ;
4. validation du format détecté ;
5. validation des dimensions ;
6. correction de l'orientation EXIF ;
7. conversion dans un mode colorimétrique sûr ;
8. redimensionnement ;
9. réencodage complet en WebP ;
10. génération d'un nouveau nom aléatoire.

Le réencodage complet supprime notamment :

- le nom original ;
- les métadonnées EXIF ;
- les coordonnées GPS éventuelles ;
- les commentaires intégrés ;
- les profils et informations non nécessaires.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import (
    Image,
    ImageOps,
    UnidentifiedImageError,
)


# Formats réellement autorisés après détection par Pillow.
#
# Nous n'accordons aucune confiance à l'extension ou au Content-Type
# transmis par le navigateur.
ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


@dataclass(frozen=True)
class ProcessedImage:
    """
    Résultat immuable du traitement d'une image.

    filename
        Nouveau nom généré par le serveur.

    content
        Contenu WebP prêt à être remis à Django.

    width / height
        Dimensions finales du fichier.
    """

    filename: str
    content: ContentFile
    width: int
    height: int


def validate_uploaded_size(uploaded_file) -> None:
    """
    Vérifie la taille déclarée du fichier avant son décodage.

    Cette validation réduit la consommation inutile de mémoire
    et de temps processeur.
    """

    maximum_size = int(
        settings.PROFILE_PHOTO_MAX_BYTES
    )

    uploaded_size = getattr(
        uploaded_file,
        "size",
        None,
    )

    if uploaded_size is None:
        raise ValidationError(
            {
                "image": (
                    "La taille du fichier ne peut pas être déterminée."
                )
            }
        )

    if uploaded_size <= 0:
        raise ValidationError(
            {
                "image": "Le fichier transmis est vide."
            }
        )

    if uploaded_size > maximum_size:
        maximum_megabytes = round(
            maximum_size / (1024 * 1024),
            1,
        )

        raise ValidationError(
            {
                "image": (
                    f"La photo ne peut pas dépasser "
                    f"{maximum_megabytes} Mio."
                )
            }
        )


def open_and_verify_image(uploaded_file) -> Image.Image:
    """
    Ouvre puis vérifie la structure réelle du fichier.

    Image.verify() analyse la structure du fichier sans se fier
    à son nom ou à son extension.

    Le fichier est ensuite rouvert, car verify() rend l'objet initial
    inutilisable pour les traitements suivants.
    """

    try:
        uploaded_file.seek(0)

        verification_image = Image.open(
            uploaded_file
        )

        detected_format = (
            verification_image.format or ""
        ).upper()

        if detected_format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                {
                    "image": (
                        "Format refusé. Utilisez une image "
                        "JPEG, PNG ou WebP."
                    )
                }
            )

        verification_image.verify()

        uploaded_file.seek(0)

        image = Image.open(
            uploaded_file
        )

        # Force le décodage complet du contenu.
        #
        # Certaines erreurs ne sont détectées qu'au moment du load().
        image.load()

        return image

    except ValidationError:
        raise

    except Image.DecompressionBombError as exc:
        raise ValidationError(
            {
                "image": (
                    "Les dimensions de cette image sont dangereusement "
                    "élevées."
                )
            }
        ) from exc

    except Image.DecompressionBombWarning as exc:
        raise ValidationError(
            {
                "image": (
                    "Les dimensions de cette image sont trop élevées."
                )
            }
        ) from exc

    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise ValidationError(
            {
                "image": (
                    "Le fichier transmis n'est pas une image valide."
                )
            }
        ) from exc


def validate_image_dimensions(
    image: Image.Image,
) -> None:
    """
    Vérifie les dimensions minimales et maximales.

    La limite maximale protège contre la consommation excessive
    de mémoire pendant la décompression.
    """

    width, height = image.size

    minimum_width = int(
        settings.PROFILE_PHOTO_MIN_WIDTH
    )
    minimum_height = int(
        settings.PROFILE_PHOTO_MIN_HEIGHT
    )

    maximum_width = int(
        settings.PROFILE_PHOTO_MAX_WIDTH
    )
    maximum_height = int(
        settings.PROFILE_PHOTO_MAX_HEIGHT
    )

    if (
        width < minimum_width
        or height < minimum_height
    ):
        raise ValidationError(
            {
                "image": (
                    "La photo doit mesurer au minimum "
                    f"{minimum_width} × {minimum_height} pixels."
                )
            }
        )

    if (
        width > maximum_width
        or height > maximum_height
    ):
        raise ValidationError(
            {
                "image": (
                    "La photo dépasse les dimensions maximales "
                    f"de {maximum_width} × {maximum_height} pixels."
                )
            }
        )


def convert_to_safe_rgb(
    image: Image.Image,
) -> Image.Image:
    """
    Corrige l'orientation et produit une image RGB sûre.

    ImageOps.exif_transpose() applique l'orientation indiquée
    dans les métadonnées avant que celles-ci soient supprimées.
    """

    oriented_image = ImageOps.exif_transpose(
        image
    )

    # Gestion correcte des images transparentes.
    if oriented_image.mode in {
        "RGBA",
        "LA",
    }:
        rgba_image = oriented_image.convert(
            "RGBA"
        )

        background = Image.new(
            "RGBA",
            rgba_image.size,
            (255, 255, 255, 255),
        )

        background.alpha_composite(
            rgba_image
        )

        return background.convert(
            "RGB"
        )

    # Les images avec une palette peuvent également contenir
    # une transparence.
    if (
        oriented_image.mode == "P"
        and "transparency" in oriented_image.info
    ):
        rgba_image = oriented_image.convert(
            "RGBA"
        )

        background = Image.new(
            "RGBA",
            rgba_image.size,
            (255, 255, 255, 255),
        )

        background.alpha_composite(
            rgba_image
        )

        return background.convert(
            "RGB"
        )

    return oriented_image.convert(
        "RGB"
    )


def resize_image(
    image: Image.Image,
) -> Image.Image:
    """
    Réduit l'image sans l'agrandir ni modifier son ratio.

    thumbnail() conserve les proportions d'origine.
    """

    maximum_output_width = int(
        settings.PROFILE_PHOTO_OUTPUT_MAX_WIDTH
    )
    maximum_output_height = int(
        settings.PROFILE_PHOTO_OUTPUT_MAX_HEIGHT
    )

    image.thumbnail(
        (
            maximum_output_width,
            maximum_output_height,
        ),
        Image.Resampling.LANCZOS,
    )

    return image


def encode_webp(
    image: Image.Image,
) -> BytesIO:
    """
    Réencode entièrement l'image dans un nouveau fichier WebP.

    Aucun EXIF ni nom original n'est transmis à save().
    """

    output_buffer = BytesIO()

    image.save(
        output_buffer,
        format="WEBP",
        quality=int(
            settings.PROFILE_PHOTO_WEBP_QUALITY
        ),
        method=6,
        optimize=True,
    )

    output_buffer.seek(0)

    return output_buffer


def process_profile_photo(
    uploaded_file,
) -> ProcessedImage:
    """
    Exécute la totalité du pipeline sécurisé.
    """

    validate_uploaded_size(
        uploaded_file
    )

    image = open_and_verify_image(
        uploaded_file
    )

    try:
        validate_image_dimensions(
            image
        )

        safe_image = convert_to_safe_rgb(
            image
        )

        resized_image = resize_image(
            safe_image
        )

        output_buffer = encode_webp(
            resized_image
        )

        final_width, final_height = (
            resized_image.size
        )

        random_filename = (
            f"{uuid4().hex}.webp"
        )

        content = ContentFile(
            output_buffer.getvalue(),
            name=Path(
                random_filename
            ).name,
        )

        return ProcessedImage(
            filename=random_filename,
            content=content,
            width=final_width,
            height=final_height,
        )

    finally:
        image.close()
