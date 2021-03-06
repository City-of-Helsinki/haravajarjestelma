# Generated by Django 2.2.8 on 2020-02-22 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("areas", "0005_allow_multiple_users_per_contract_zone")]

    operations = [
        migrations.AddField(
            model_name="contractzone",
            name="secondary_contact_person",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="secondary contact person"
            ),
        ),
        migrations.AddField(
            model_name="contractzone",
            name="secondary_email",
            field=models.EmailField(
                blank=True, max_length=254, verbose_name="secondary email"
            ),
        ),
        migrations.AddField(
            model_name="contractzone",
            name="secondary_phone",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="secondary phone"
            ),
        ),
    ]
