from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challans", "0003_fulfilment_and_vehicle_search"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="challandetail",
            name="uniq_user_challan_vehicle",
        ),
        migrations.AddConstraint(
            model_name="challandetail",
            constraint=models.UniqueConstraint(
                fields=("challan_number", "source_name"),
                name="uniq_challan_number_source",
            ),
        ),
    ]
