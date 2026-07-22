
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0002_alter_profile_is_discoverable_searchpreferences"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchpreferences",
            name="only_profiles_with_photos",
            field=models.BooleanField(default=False),
        ),
    ]
