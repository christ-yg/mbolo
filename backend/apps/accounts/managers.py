from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Gestionnaire chargé de créer les utilisateurs et superutilisateurs.

    Il centralise notamment :
    - la normalisation des adresses e-mail ;
    - le hachage correct des mots de passe ;
    - les contrôles obligatoires des comptes administrateurs.
    """

    use_in_migrations = True

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        if not email:
            raise ValueError("Une adresse e-mail est obligatoire.")

        email = self.normalize_email(email).strip().lower()

        user = self.model(
            email=email,
            **extra_fields,
        )

        # set_password applique le moteur de hachage Django.
        # Un mot de passe ne doit jamais être enregistré directement.
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Un superutilisateur doit avoir is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Un superutilisateur doit avoir is_superuser=True."
            )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )
