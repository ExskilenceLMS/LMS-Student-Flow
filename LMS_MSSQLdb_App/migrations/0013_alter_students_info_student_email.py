# Generated by Django 4.1.13 on 2025-04-07 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0012_course_plan_details_batch_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='students_info',
            name='student_email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
