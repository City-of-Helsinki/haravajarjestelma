# Generated by Django 2.1.3 on 2019-01-10 19:52

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ContractZone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('boundary', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, verbose_name='boundary')),
            ],
            options={
                'verbose_name': 'contract zone',
                'verbose_name_plural': 'contract zones',
                'ordering': ('id',),
            },
        ),
    ]