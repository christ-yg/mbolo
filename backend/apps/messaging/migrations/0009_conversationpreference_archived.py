from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0008_conversationpreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversationpreference",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
