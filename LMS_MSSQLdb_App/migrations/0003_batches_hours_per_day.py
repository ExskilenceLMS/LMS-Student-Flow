# Generated by Django 4.1.13 on 2025-05-05 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0002_batches_saturday_holiday_batches_sunday_holiday'),
    ]

    operations = [
        migrations.AddField(
            model_name='batches',
            name='hours_per_day',
            field=models.IntegerField(default=0),
        ),
    ]
