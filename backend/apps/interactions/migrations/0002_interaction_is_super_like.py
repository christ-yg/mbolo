from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("interactions", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="interaction",
            name="is_super_like",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
