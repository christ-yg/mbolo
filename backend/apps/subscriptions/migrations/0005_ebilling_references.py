from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0004_profileboost"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymenttransaction",
            name="provider_bill_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=128,
            ),
        ),
        migrations.AddField(
            model_name="paymenttransaction",
            name="provider_ussd_push_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=128,
            ),
        ),
    ]
