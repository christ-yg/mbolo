"""
Signaux du module Photos.

Ce fichier garantit que le fichier physique d'une photo est supprimé
lorsque sa ligne ProfilePhoto disparaît de la base de données.

La suppression est programmée après la validation de la transaction
PostgreSQL grâce à transaction.on_commit().
"""

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ProfilePhoto


@receiver(
    post_delete,
    sender=ProfilePhoto,
)
def delete_profile_photo_file(
    sender,
    instance: ProfilePhoto,
    **kwargs,
) -> None:
    """
    Supprime le fichier associé après suppression de la ligne SQL.

    Nous attendons le commit de la transaction afin d'éviter
    la situation suivante :

    1. le fichier est supprimé ;
    2. la transaction PostgreSQL échoue ;
    3. la ligne revient après rollback ;
    4. mais le fichier n'existe plus.

    transaction.on_commit() réduit ce risque d'incohérence.
    """

    del sender
    del kwargs

    if not instance.image:
        return

    storage = instance.image.storage

    file_name = instance.image.name

    if not file_name:
        return

    transaction.on_commit(
        lambda: storage.delete(
            file_name
        )
    )
