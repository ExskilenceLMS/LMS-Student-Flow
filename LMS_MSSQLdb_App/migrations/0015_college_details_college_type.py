# Generated by Django 4.1.13 on 2025-04-09 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0014_alter_students_info_student_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='college_details',
            name='college_type',
            field=models.CharField(default='others', max_length=20),
            preserve_default=False,
        ),
    ]
