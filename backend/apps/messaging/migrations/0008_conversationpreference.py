import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("messaging", "0007_message_edited_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("pinned", models.BooleanField(default=False)),
                ("muted", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="preferences", to="messaging.conversation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversation_preferences", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "messaging_conversation_preference"},
        ),
        migrations.AddConstraint(
            model_name="conversationpreference",
            constraint=models.UniqueConstraint(fields=("conversation", "user"), name="unique_conversation_preference_per_user"),
        ),
    ]
