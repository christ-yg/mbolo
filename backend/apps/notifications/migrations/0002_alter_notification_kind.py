from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("message", "Message"),
                    ("match", "Nouveau match"),
                    ("like", "Like"),
                    ("super_like", "Super Like"),
                    ("security", "Sécurité"),
                    ("system", "Système"),
                ],
                db_index=True,
                max_length=24,
            ),
        ),
    ]
