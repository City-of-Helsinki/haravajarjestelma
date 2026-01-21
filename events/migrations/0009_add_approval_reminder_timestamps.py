from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0008_add_event_is_anonymized"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="approval_creation_reminder_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                editable=False,
                verbose_name="approval creation reminder sent at",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="approval_deadline_reminder_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                editable=False,
                verbose_name="approval deadline reminder sent at",
            ),
        ),
    ]
