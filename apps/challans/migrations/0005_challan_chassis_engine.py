from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challans", "0004_challan_unique_by_number_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="challandetail",
            name="chassis_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="challandetail",
            name="engine_number",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
