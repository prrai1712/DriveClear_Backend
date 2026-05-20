from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0003_fulfilment_and_vehicle_search"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehicleChallanFetchConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vehicle_number", models.CharField(db_index=True, max_length=12, unique=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("challanpay", "ChallanPay")],
                        db_index=True,
                        default="challanpay",
                        max_length=32,
                    ),
                ),
                ("last_success_fetch_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("last_fetch_challan_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "vehicle_challan_fetch_config",
                "indexes": [
                    models.Index(fields=["source", "last_success_fetch_at"], name="vehicle_cha_source_0a8f2d_idx"),
                ],
            },
        ),
    ]
