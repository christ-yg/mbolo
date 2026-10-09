from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0009_conversationpreference_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversationpreference",
            name="marked_unread",
            field=models.BooleanField(default=False),
        ),
    ]
