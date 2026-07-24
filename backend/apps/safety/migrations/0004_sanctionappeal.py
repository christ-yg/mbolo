from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0003_moderationsanction"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SanctionAppeal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("message", models.TextField(max_length=2000)),
                ("status", models.CharField(choices=[("pending", "En attente"), ("accepted", "Acceptée"), ("rejected", "Refusée")], db_index=True, default="pending", max_length=16)),
                ("moderator_note", models.TextField(blank=True, default="", max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_sanction_appeals", to=settings.AUTH_USER_MODEL)),
                ("sanction", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="appeal", to="safety.moderationsanction")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sanction_appeals", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "safety_sanction_appeal",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="sanctionappeal",
            index=models.Index(fields=["status", "-created_at"], name="appeal_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="sanctionappeal",
            index=models.Index(fields=["user", "-created_at"], name="appeal_user_created_idx"),
        ),
    ]
