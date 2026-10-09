from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("messaging", "0006_message_deleted_at")]

    operations = [
        migrations.AddField(
            model_name="message",
            name="edited_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
