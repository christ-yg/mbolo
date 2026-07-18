"""
Services métier du module Safety.

La logique de blocage est isolée des vues HTTP afin de pouvoir être
réutilisée plus tard par :

- l'application web ;
- l'application mobile ;
- une interface de modération ;
- une tâche asynchrone ;
- une commande d'administration.

Les opérations critiques sont protégées par :

- transaction.atomic() ;
- select_for_update() ;
- contraintes PostgreSQL ;
- messages d'erreur génériques ;
- désactivation automatique des matchs.
"""

from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q

from apps.interactions.models import Match
from apps.profiles.models import Profile

from .models import Block


@dataclass(frozen=True)
class BlockResult:
    """
    Résultat immuable d'une opération de blocage.

    block
        Objet Block créé ou déjà existant.

    created
        True si le blocage vient d'être créé.
        False si la même relation existait déjà.

    deactivated_matches
        Nombre de matchs désactivés par l'opération.
    """

    block: Block
    created: bool
    deactivated_matches: int


def validate_block_target(
    *,
    blocker,
    blocked_user_id: UUID,
):
    """
    Vérifie que l'utilisateur ciblé existe et peut être bloqué.

    Nous utilisons un message générique lorsque la cible n'existe pas,
    afin de limiter les possibilités d'énumération des comptes.
    """

    user_model = blocker.__class__

    try:
        blocked_user = (
            user_model.objects
            .select_for_update()
            .get(
                id=blocked_user_id,
            )
        )
    except user_model.DoesNotExist as exc:
        raise ValidationError(
            "L'utilisateur demandé n'est pas disponible."
        ) from exc

    if blocked_user.id == blocker.id:
        raise ValidationError(
            "Vous ne pouvez pas vous bloquer vous-même."
        )

    return blocked_user


def deactivate_matches_between_users(
    *,
    first_user,
    second_user,
) -> int:
    """
    Désactive tous les matchs actifs entre deux utilisateurs.

    Normalement, une paire ne possède qu'un match grâce à la contrainte
    d'unicité. Nous utilisons néanmoins update() pour une défense robuste
    face à d'anciennes données ou à une migration historique.
    """

    try:
        first_profile = Profile.objects.get(
            user=first_user,
        )

        second_profile = Profile.objects.get(
            user=second_user,
        )
    except Profile.DoesNotExist:
        # L'absence de profil n'empêche pas le blocage du compte.
        return 0

    matches = Match.objects.filter(
        Q(
            profile_one=first_profile,
            profile_two=second_profile,
        )
        | Q(
            profile_one=second_profile,
            profile_two=first_profile,
        ),
        is_active=True,
    )

    return matches.update(
        is_active=False,
    )


@transaction.atomic
def create_block(
    *,
    blocker,
    blocked_user_id: UUID,
) -> BlockResult:
    """
    Crée un blocage dans une transaction atomique.

    Principe :

        soit toutes les opérations réussissent ;
        soit PostgreSQL annule tout.

    Le blocage reste idempotent :

    appeler deux fois la même opération ne crée pas deux lignes.
    """

    if not blocker.is_authenticated:
        raise ValidationError(
            "Une authentification est requise."
        )

    if not blocker.is_active or blocker.is_suspended:
        raise ValidationError(
            "Ce compte ne peut pas effectuer cette action."
        )

    blocked_user = validate_block_target(
        blocker=blocker,
        blocked_user_id=blocked_user_id,
    )

    existing_block = (
        Block.objects
        .select_for_update()
        .filter(
            blocker=blocker,
            blocked_user=blocked_user,
        )
        .first()
    )

    if existing_block is not None:
        block = existing_block
        created = False

    else:
        try:
            # La transaction imbriquée crée un savepoint.
            #
            # Si une requête concurrente crée la même ligne, seule cette
            # portion est annulée, pas la transaction principale.
            with transaction.atomic():
                block = Block.objects.create(
                    blocker=blocker,
                    blocked_user=blocked_user,
                )

            created = True

        except IntegrityError:
            block = (
                Block.objects
                .select_for_update()
                .get(
                    blocker=blocker,
                    blocked_user=blocked_user,
                )
            )

            created = False

    deactivated_matches = deactivate_matches_between_users(
        first_user=blocker,
        second_user=blocked_user,
    )

    return BlockResult(
        block=block,
        created=created,
        deactivated_matches=deactivated_matches,
    )


@transaction.atomic
def delete_block(
    *,
    blocker,
    block_id: UUID,
) -> None:
    """
    Supprime uniquement un blocage appartenant à l'utilisateur connecté.

    L'utilisation combinée de blocker et block_id empêche une IDOR :

    un utilisateur ne peut pas supprimer le blocage créé par quelqu'un
    d'autre en connaissant ou en devinant son UUID.
    """

    try:
        block = (
            Block.objects
            .select_for_update()
            .get(
                id=block_id,
                blocker=blocker,
            )
        )
    except Block.DoesNotExist as exc:
        # Message générique : absence et interdiction produisent
        # le même comportement externe.
        raise ValidationError(
            "Le blocage demandé n'est pas disponible."
        ) from exc

    block.delete()


def users_are_blocked(
    *,
    first_user,
    second_user,
) -> bool:
    """
    Retourne True lorsqu'un blocage existe dans l'un des deux sens.

    Exemple :

        A bloque B => True
        B bloque A => True

    Les effets applicatifs sont donc bidirectionnels.
    """

    return Block.objects.filter(
        Q(
            blocker=first_user,
            blocked_user=second_user,
        )
        | Q(
            blocker=second_user,
            blocked_user=first_user,
        )
    ).exists()
