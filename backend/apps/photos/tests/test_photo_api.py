"""
Tests fonctionnels et de sécurité de l'API Photos de Mbolo.

Ce fichier vérifie notamment :

- l'authentification obligatoire ;
- la protection CSRF pour les opérations d'écriture ;
- la validation réelle du contenu des images ;
- le rejet des faux fichiers image ;
- les dimensions minimales ;
- le réencodage sécurisé en WebP ;
- la suppression du nom original du fichier ;
- la suppression des métadonnées EXIF ;
- l'attribution automatique de la première photo principale ;
- la limite maximale de six photos ;
- l'unicité des positions dans la galerie ;
- l'unicité de la photo principale ;
- la protection contre les IDOR ;
- la réattribution de la photo principale après suppression ;
- la suppression du fichier physique après validation SQL ;
- l'isolation des photos entre les utilisateurs.

Les fichiers sont enregistrés dans un répertoire média temporaire
pendant les tests. Aucun fichier de test ne doit donc rester dans
le dossier media/ réel du projet.
"""

from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.profiles.models import Profile

from ..models import ProfilePhoto


# Récupère dynamiquement le modèle utilisateur configuré dans Django.
#
# Dans Mbolo, il s'agit du modèle personnalisé :
#
#     apps.accounts.models.User
#
# Cette méthode est préférable à l'import direct du modèle.
User = get_user_model()


def years_ago(years: int) -> date:
    """
    Retourne une date de naissance correspondant à un âge donné.

    Exemple :

        years_ago(30)

    produit une date située approximativement trente ans avant
    la date d'exécution du test.

    Le cas particulier du 29 février est traité afin que les tests
    fonctionnent aussi pendant une année non bissextile.
    """

    today = date.today()

    try:
        return today.replace(
            year=today.year - years,
        )
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


def build_test_image(
    *,
    filename: str = "photo.jpg",
    width: int = 640,
    height: int = 640,
    image_format: str = "JPEG",
) -> SimpleUploadedFile:
    """
    Génère une véritable image en mémoire pour les tests.

    Aucun fichier externe n'est nécessaire.

    Paramètres
    ----------
    filename:
        Nom présenté à l'API comme nom original du fichier.

    width / height:
        Dimensions de l'image en pixels.

    image_format:
        Format réellement encodé par Pillow :
        JPEG, PNG ou WEBP.

    Sécurité
    --------
    Le nom et l'extension peuvent être différents du contenu réel.
    Cela permet de vérifier que notre backend inspecte effectivement
    le fichier au lieu de faire confiance à son extension.
    """

    # BytesIO constitue un fichier temporaire conservé en mémoire.
    buffer = BytesIO()

    # Création d'une image RGB simple.
    #
    # La couleur n'a aucune importance fonctionnelle.
    image = Image.new(
        "RGB",
        (width, height),
        (120, 80, 160),
    )

    # Encodage réel de l'image dans le format demandé.
    image.save(
        buffer,
        format=image_format,
    )

    # Libération explicite des ressources Pillow.
    image.close()

    # Retour au début du flux avant lecture.
    buffer.seek(0)

    content_type_by_format = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    # SimpleUploadedFile imite un fichier reçu depuis un navigateur.
    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type=content_type_by_format[
            image_format
        ],
    )


class ProfilePhotoAPITests(TestCase):
    """
    Tests des endpoints de gestion des photos de profil.

    Endpoints concernés :

        GET    /api/v1/profiles/photos/
        POST   /api/v1/profiles/photos/
        PATCH  /api/v1/profiles/photos/<uuid>/
        DELETE /api/v1/profiles/photos/<uuid>/
    """

    def setUp(self) -> None:
        """
        Prépare un environnement isolé avant chaque test.

        Nous créons :

        - un répertoire média temporaire ;
        - un client API avec contrôles CSRF réels ;
        - un utilisateur propriétaire ;
        - un second utilisateur pour tester les IDOR ;
        - un profil adulte pour chaque utilisateur.

        Le stockage temporaire empêche les tests d'écrire dans
        backend/media/ et facilite le nettoyage automatique.
        """

        # Création d'un dossier temporaire propre à ce test.
        self.temporary_media = TemporaryDirectory()

        # Remplacement temporaire des paramètres de stockage.
        #
        # Ces réglages sont automatiquement restaurés dans tearDown().
        self.media_override = override_settings(
            MEDIA_ROOT=self.temporary_media.name,
            PROFILE_PHOTO_MAX_COUNT=6,
            PROFILE_PHOTO_MAX_BYTES=8 * 1024 * 1024,
            PROFILE_PHOTO_MIN_WIDTH=320,
            PROFILE_PHOTO_MIN_HEIGHT=320,
            PROFILE_PHOTO_MAX_WIDTH=6000,
            PROFILE_PHOTO_MAX_HEIGHT=6000,
            PROFILE_PHOTO_OUTPUT_MAX_WIDTH=1600,
            PROFILE_PHOTO_OUTPUT_MAX_HEIGHT=1600,
            PROFILE_PHOTO_WEBP_QUALITY=88,
        )

        self.media_override.enable()

        # enforce_csrf_checks=True force le client de test
        # à respecter les contrôles CSRF comme un véritable navigateur.
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

        # Résolution des routes Django par leur nom.
        self.list_url = reverse(
            "photos:photo-list-create",
        )

        self.csrf_url = reverse(
            "core:csrf-token",
        )

        self.password = (
            "Strong-Photo-Test-Password-2026!"
        )

        # Premier utilisateur : propriétaire des photos testées.
        self.user, self.profile = (
            self.create_user_with_profile(
                email="photo-owner@example.com",
                display_name="Propriétaire",
            )
        )

        # Deuxième utilisateur : utilisé pour les tests d'isolation
        # et de protection contre les IDOR.
        self.other_user, self.other_profile = (
            self.create_user_with_profile(
                email="other-photo-owner@example.com",
                display_name="Autre propriétaire",
            )
        )

    def tearDown(self) -> None:
        """
        Nettoie les ressources après chaque test.

        Les paramètres Django sont restaurés et le répertoire
        média temporaire est supprimé.
        """

        self.media_override.disable()

        self.temporary_media.cleanup()

    def create_user_with_profile(
        self,
        *,
        email: str,
        display_name: str,
    ):
        """
        Crée un utilisateur autorisé à gérer des photos.

        Le compte est :

        - actif ;
        - non suspendu ;
        - vérifié par e-mail.

        Un profil adulte complet est également créé.
        """

        user = User.objects.create_user(
            email=email,
            password=self.password,
            is_active=True,
            is_suspended=False,
            is_email_verified=True,
        )

        profile = Profile.objects.create(
            user=user,
            display_name=display_name,
            birth_date=years_ago(30),
            gender="man",
            city="libreville",
            biography=(
                "Profil destiné aux tests sécurisés des photos."
            ),
            dating_intent="serious_relationship",
            is_discoverable=True,
        )

        return user, profile

    def authenticate(
        self,
        *,
        user=None,
    ) -> str:
        """
        Authentifie le client et retourne un jeton CSRF valide.

        SessionAuthentication exige :

        1. une session Django authentifiée ;
        2. un jeton CSRF pour les opérations d'écriture.
        """

        authenticated_user = user or self.user

        # force_login crée une session Django pour l'utilisateur.
        self.client.force_login(
            authenticated_user,
        )

        # L'endpoint CSRF crée le cookie et retourne le jeton.
        response = self.client.get(
            self.csrf_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return response.data["csrfToken"]

    def upload_photo(
        self,
        *,
        csrf_token: str,
        image=None,
        position=None,
        is_primary=None,
    ):
        """
        Téléverse une photo par requête multipart/form-data.

        Cette méthode évite de répéter le même code dans chaque test.
        """

        payload = {
            "image": image or build_test_image(),
        }

        if position is not None:
            # Dans une requête multipart, les valeurs textuelles
            # sont généralement transmises comme chaînes.
            payload["position"] = str(position)

        if is_primary is not None:
            payload["is_primary"] = (
                "true"
                if is_primary
                else "false"
            )

        return self.client.post(
            self.list_url,
            payload,
            format="multipart",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def create_photo_directly(
        self,
        *,
        profile: Profile,
        position: int,
        is_primary: bool,
    ) -> ProfilePhoto:
        """
        Crée directement une photo dans le modèle.

        Cette méthode est utilisée pour préparer certains tests IDOR.

        La création directe n'est pas utilisée pour tester le pipeline
        d'upload : elle sert uniquement à préparer une photo appartenant
        à un autre utilisateur.
        """

        image = build_test_image(
            filename=f"direct-{uuid4().hex}.jpg",
        )

        photo = ProfilePhoto(
            profile=profile,
            position=position,
            is_primary=is_primary,
        )

        photo.image.save(
            image.name,
            image,
            save=False,
        )

        photo.save()

        return photo

    def test_anonymous_user_cannot_upload_photo(
        self,
    ) -> None:
        """
        Un utilisateur non authentifié ne peut pas ajouter de photo.
        """

        response = self.client.post(
            self.list_url,
            {
                "image": build_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            0,
        )

    def test_upload_requires_csrf_token(
        self,
    ) -> None:
        """
        Une session authentifiée sans jeton CSRF doit être refusée.
        """

        self.client.force_login(
            self.user,
        )

        response = self.client.post(
            self.list_url,
            {
                "image": build_test_image(),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            0,
        )

    def test_valid_image_is_reencoded_as_webp(
        self,
    ) -> None:
        """
        Une image JPEG valide doit être réencodée en WebP.

        Le nom fourni par le client ne doit pas être conservé.
        """

        csrf_token = self.authenticate()

        response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                filename="../../photo-dangeruse.jpg",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        photo = ProfilePhoto.objects.get()

        # Vérification du nouveau format.
        self.assertTrue(
            photo.image.name.endswith(".webp")
        )

        # Le nom original et son chemin dangereux doivent disparaître.
        self.assertNotIn(
            "photo-dangeruse",
            photo.image.name,
        )

        self.assertNotIn(
            "..",
            photo.image.name,
        )

        # La première photo devient automatiquement principale.
        self.assertTrue(
            photo.is_primary
        )

        file_path = Path(
            photo.image.path
        )

        self.assertTrue(
            file_path.exists()
        )

        # Vérification directe du fichier produit.
        with Image.open(file_path) as image:
            self.assertEqual(
                image.format,
                "WEBP",
            )

            self.assertEqual(
                image.size,
                (640, 640),
            )

            # Le fichier réencodé ne doit conserver aucun EXIF.
            self.assertEqual(
                dict(image.getexif()),
                {},
            )

    def test_fake_image_is_rejected(
        self,
    ) -> None:
        """
        Un fichier texte renommé en .jpg doit être refusé.

        Le Content-Type transmis par le client ne constitue pas
        une preuve que le fichier est réellement une image.
        """

        csrf_token = self.authenticate()

        fake_image = SimpleUploadedFile(
            "fake.jpg",
            b"ceci n'est absolument pas une image",
            content_type="image/jpeg",
        )

        response = self.upload_photo(
            csrf_token=csrf_token,
            image=fake_image,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            0,
        )

    def test_small_image_is_rejected(
        self,
    ) -> None:
        """
        Une image inférieure à 320 × 320 pixels doit être refusée.
        """

        csrf_token = self.authenticate()

        response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                width=200,
                height=200,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            0,
        )

    def test_first_photo_becomes_primary_automatically(
        self,
    ) -> None:
        """
        La première photo devient principale même si false est envoyé.

        Une galerie non vide doit toujours posséder une photo principale.
        """

        csrf_token = self.authenticate()

        response = self.upload_photo(
            csrf_token=csrf_token,
            is_primary=False,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        photo = ProfilePhoto.objects.get()

        self.assertTrue(
            photo.is_primary
        )

        self.assertEqual(
            photo.position,
            0,
        )

    def test_seventh_photo_is_rejected(
        self,
    ) -> None:
        """
        Un profil ne peut pas posséder plus de six photos.
        """

        csrf_token = self.authenticate()

        # Création des six photos autorisées.
        for position in range(6):
            response = self.upload_photo(
                csrf_token=csrf_token,
                image=build_test_image(
                    filename=f"photo-{position}.jpg",
                ),
                position=position,
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
            )

        # La septième photo doit être refusée.
        seventh_response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                filename="photo-7.jpg",
            ),
        )

        self.assertEqual(
            seventh_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            6,
        )

    def test_duplicate_position_is_rejected(
        self,
    ) -> None:
        """
        Deux photos d'un même profil ne peuvent pas utiliser
        la même position.
        """

        csrf_token = self.authenticate()

        first_response = self.upload_photo(
            csrf_token=csrf_token,
            position=2,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                filename="second.jpg",
            ),
            position=2,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            ProfilePhoto.objects.count(),
            1,
        )

    def test_promoting_photo_removes_old_primary(
        self,
    ) -> None:
        """
        La promotion d'une nouvelle photo principale doit rétrograder
        automatiquement l'ancienne.
        """

        csrf_token = self.authenticate()

        first_response = self.upload_photo(
            csrf_token=csrf_token,
            position=0,
        )

        second_response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                filename="second.jpg",
            ),
            position=1,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        first_id = first_response.data["data"]["id"]
        second_id = second_response.data["data"]["id"]

        detail_url = reverse(
            "photos:photo-detail",
            kwargs={
                "photo_id": second_id,
            },
        )

        patch_response = self.client.patch(
            detail_url,
            {
                "is_primary": True,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            patch_response.status_code,
            status.HTTP_200_OK,
        )

        first_photo = ProfilePhoto.objects.get(
            id=first_id,
        )

        second_photo = ProfilePhoto.objects.get(
            id=second_id,
        )

        self.assertFalse(
            first_photo.is_primary
        )

        self.assertTrue(
            second_photo.is_primary
        )

        # La contrainte logique doit rester vraie :
        # exactement une photo principale.
        self.assertEqual(
            ProfilePhoto.objects.filter(
                profile=self.profile,
                is_primary=True,
            ).count(),
            1,
        )

    def test_user_cannot_patch_foreign_photo(
        self,
    ) -> None:
        """
        Un utilisateur ne peut pas modifier la photo d'un autre compte.

        Ce test couvre une tentative d'IDOR par modification d'UUID.
        """

        foreign_photo = self.create_photo_directly(
            profile=self.other_profile,
            position=0,
            is_primary=True,
        )

        csrf_token = self.authenticate()

        detail_url = reverse(
            "photos:photo-detail",
            kwargs={
                "photo_id": foreign_photo.id,
            },
        )

        response = self.client.patch(
            detail_url,
            {
                "position": 3,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        foreign_photo.refresh_from_db()

        # La photo étrangère ne doit subir aucune modification.
        self.assertEqual(
            foreign_photo.position,
            0,
        )

    def test_user_cannot_delete_foreign_photo(
        self,
    ) -> None:
        """
        Un utilisateur ne peut pas supprimer la photo d'un autre compte.

        Ce test couvre une tentative d'IDOR sur DELETE.
        """

        foreign_photo = self.create_photo_directly(
            profile=self.other_profile,
            position=0,
            is_primary=True,
        )

        csrf_token = self.authenticate()

        detail_url = reverse(
            "photos:photo-detail",
            kwargs={
                "photo_id": foreign_photo.id,
            },
        )

        response = self.client.delete(
            detail_url,
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # La photo étrangère doit toujours exister.
        self.assertTrue(
            ProfilePhoto.objects.filter(
                id=foreign_photo.id,
            ).exists()
        )

    def test_deleting_primary_promotes_remaining_photo(
        self,
    ) -> None:
        """
        La suppression de la photo principale doit produire
        deux effets cohérents :

        1. la photo restante devient automatiquement principale ;
        2. le fichier physique de l'ancienne photo est supprimé.

        Le signal post_delete utilise transaction.on_commit().
        Le contexte captureOnCommitCallbacks doit donc entourer
        la requête DELETE qui enregistre ce callback.
        """

        csrf_token = self.authenticate()

        # Création de la première photo.
        #
        # Comme il s'agit de la première photo du profil,
        # elle devient automatiquement principale.
        first_response = self.upload_photo(
            csrf_token=csrf_token,
            position=0,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        # Création d'une seconde photo qui servira de remplaçante.
        second_response = self.upload_photo(
            csrf_token=csrf_token,
            image=build_test_image(
                filename="replacement.jpg",
            ),
            position=1,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        first_id = first_response.data["data"]["id"]
        second_id = second_response.data["data"]["id"]

        # Mémorisation du chemin du fichier physique avant suppression.
        first_photo = ProfilePhoto.objects.get(
            id=first_id,
        )

        first_file_path = Path(
            first_photo.image.path
        )

        # Le fichier doit exister avant l'appel DELETE.
        self.assertTrue(
            first_file_path.exists()
        )

        detail_url = reverse(
            "photos:photo-detail",
            kwargs={
                "photo_id": first_id,
            },
        )

        # IMPORTANT :
        #
        # Le contexte commence AVANT la requête DELETE.
        #
        # Il capture ainsi le callback transaction.on_commit()
        # enregistré par le signal post_delete pendant la suppression.
        with self.captureOnCommitCallbacks(
            execute=True,
        ) as callbacks:
            response = self.client.delete(
                detail_url,
                HTTP_X_CSRFTOKEN=csrf_token,
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        # Au moins un callback doit avoir été programmé :
        # celui qui supprime le fichier physique.
        self.assertGreaterEqual(
            len(callbacks),
            1,
        )

        # La ligne SQL supprimée ne doit plus exister.
        self.assertFalse(
            ProfilePhoto.objects.filter(
                id=first_id,
            ).exists()
        )

        # La seconde photo doit toujours exister.
        second_photo = ProfilePhoto.objects.get(
            id=second_id,
        )

        # Elle doit être devenue automatiquement principale.
        self.assertTrue(
            second_photo.is_primary
        )

        # Une seule photo principale doit subsister.
        self.assertEqual(
            ProfilePhoto.objects.filter(
                profile=self.profile,
                is_primary=True,
            ).count(),
            1,
        )

        # Le callback transactionnel a été exécuté.
        # Le fichier physique doit donc avoir disparu.
        self.assertFalse(
            first_file_path.exists()
        )

    def test_list_returns_only_current_user_photos(
        self,
    ) -> None:
        """
        La liste ne doit contenir que les photos du compte connecté.

        Les photos appartenant aux autres utilisateurs ne doivent
        jamais apparaître.
        """

        own_photo = self.create_photo_directly(
            profile=self.profile,
            position=0,
            is_primary=True,
        )

        foreign_photo = self.create_photo_directly(
            profile=self.other_profile,
            position=0,
            is_primary=True,
        )

        self.client.force_login(
            self.user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = {
            str(item["id"])
            for item in response.data["results"]
        }

        self.assertIn(
            str(own_photo.id),
            returned_ids,
        )

        self.assertNotIn(
            str(foreign_photo.id),
            returned_ids,
        )
