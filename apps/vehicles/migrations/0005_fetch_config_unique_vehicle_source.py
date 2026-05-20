from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0004_vehicle_challan_fetch_config"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vehiclechallanfetchconfig",
            name="vehicle_number",
            field=models.CharField(db_index=True, max_length=12),
        ),
        migrations.AddConstraint(
            model_name="vehiclechallanfetchconfig",
            constraint=models.UniqueConstraint(
                fields=("vehicle_number", "source"),
                name="uniq_vehicle_fetch_config_number_source",
            ),
        ),
    ]
