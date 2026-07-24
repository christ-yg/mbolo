from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("photos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profilephoto",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("approved", "Approuvée"),
                    ("rejected", "Refusée"),
                ],
                db_index=True,
                default="approved",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="profilephoto",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("approved", "Approuvée"),
                    ("rejected", "Refusée"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="profilephoto",
            name="moderation_note",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Note interne, jamais exposée aux membres.",
            ),
        ),
        migrations.AddField(
            model_name="profilephoto",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profilephoto",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_profile_photos",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
