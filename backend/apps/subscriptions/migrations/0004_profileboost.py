import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0003_premiumprivacypreference"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileBoost",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("starts_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("ends_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profile_boosts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "subscriptions_profile_boost",
                "ordering": ("-starts_at",),
                "indexes": [models.Index(fields=["user", "starts_at"], name="sub_boost_user_started_idx")],
            },
        ),
    ]
