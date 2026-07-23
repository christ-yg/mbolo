from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0003_searchpreferences_only_profiles_with_photos"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="interests",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
