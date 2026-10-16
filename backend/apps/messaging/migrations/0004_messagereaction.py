import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0003_message_image"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageReaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("emoji", models.CharField(max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reactions", to="messaging.message")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_reactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "messaging_message_reaction",
                "indexes": [models.Index(fields=["message", "emoji"], name="msg_reaction_idx")],
                "constraints": [models.UniqueConstraint(fields=("message", "user"), name="unique_message_reaction_per_user")],
            },
        ),
    ]
