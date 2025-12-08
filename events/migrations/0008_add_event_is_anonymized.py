# Generated manually for adding is_anonymized field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0007_change_event_description_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_anonymized",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Whether this event has been anonymized for GDPR compliance",
                verbose_name="is anonymized",
            ),
        ),
    ]
