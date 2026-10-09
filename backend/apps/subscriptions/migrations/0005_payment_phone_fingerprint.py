from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0004_profileboost")]

    operations = [
        migrations.AddField(
            model_name="paymenttransaction",
            name="customer_phone_hash",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="paymenttransaction",
            name="customer_phone_masked",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
