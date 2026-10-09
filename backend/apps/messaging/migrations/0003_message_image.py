from django.db import migrations, models

import apps.messaging.models


class Migration(migrations.Migration):
    dependencies = [("messaging", "0002_message_read_at_and_more")]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="body",
            field=models.TextField(blank=True, default="", max_length=2000),
        ),
        migrations.AddField(
            model_name="message",
            name="image",
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to=apps.messaging.models.message_image_upload_path,
            ),
        ),
    ]
