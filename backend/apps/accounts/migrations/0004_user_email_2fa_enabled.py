from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_legal_consent"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_2fa_enabled",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Exige un code temporaire envoyé par e-mail "
                    "après la validation du mot de passe."
                ),
            ),
        ),
    ]
