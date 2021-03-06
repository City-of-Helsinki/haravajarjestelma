# Generated by Django 2.1.3 on 2019-01-10 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("areas", "0001_initial"),
        ("users", "0002_add_official_and_contractor_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="contract_zones",
            field=models.ManyToManyField(
                blank=True,
                related_name="contractors",
                to="areas.ContractZone",
                verbose_name="contract zones",
            ),
        )
    ]
