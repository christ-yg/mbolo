from django.db import migrations, models


def disable_legacy_verified_filter(apps, schema_editor):
    """
    L'ancien filtre signifiait « adresse e-mail vérifiée ».

    Depuis l'ajout de la vérification réelle du profil, conserver ce choix
    actif masquerait tous les profils historiques qui n'ont pas encore
    soumis de selfie. On le désactive donc une seule fois, sans attribuer
    artificiellement le nouveau badge à qui que ce soit.
    """

    SearchPreferences = apps.get_model(
        "profiles",
        "SearchPreferences",
    )
    SearchPreferences.objects.filter(
        only_verified_profiles=True,
    ).update(
        only_verified_profiles=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0005_profileverification"),
    ]

    operations = [
        migrations.AlterField(
            model_name="searchpreferences",
            name="only_verified_profiles",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(
            disable_legacy_verified_filter,
            migrations.RunPython.noop,
        ),
    ]
