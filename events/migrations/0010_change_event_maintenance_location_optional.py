from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0009_add_approval_reminder_timestamps"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="maintenance_location",
            field=models.TextField(blank=True, verbose_name="maintenance location"),
        ),
    ]
