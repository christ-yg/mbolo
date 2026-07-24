from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_suspension_until"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="terms_accepted_at",
            field=models.DateTimeField(
                blank=True,
                editable=False,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="terms_version",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="privacy_version",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                max_length=20,
            ),
        ),
    ]
