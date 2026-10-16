from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("messaging", "0005_message_reply_to")]

    operations = [
        migrations.AddField(
            model_name="message",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
