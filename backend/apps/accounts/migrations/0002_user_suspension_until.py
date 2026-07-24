from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="suspension_until",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text=(
                    "Date de fin d'une suspension temporaire. "
                    "Une valeur vide avec is_suspended=True représente "
                    "une suspension sans échéance."
                ),
                null=True,
            ),
        ),
    ]
