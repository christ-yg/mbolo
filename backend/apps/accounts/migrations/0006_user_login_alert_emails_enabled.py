from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Active par défaut les e-mails d'alerte pour préserver le niveau
    de protection actuel des comptes existants.
    """

    dependencies = [
        ("accounts", "0005_loginactivity"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="login_alert_emails_enabled",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Autorise l'envoi d'un e-mail lorsqu'une connexion "
                    "inhabituelle est détectée. Les notifications internes "
                    "de sécurité restent toujours actives."
                ),
            ),
        ),
    ]
