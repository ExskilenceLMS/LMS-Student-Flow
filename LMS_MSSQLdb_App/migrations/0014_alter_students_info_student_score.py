# Generated by Django 4.1.13 on 2025-04-08 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0013_alter_students_info_student_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='students_info',
            name='student_score',
            field=models.CharField(default=0, max_length=20),
        ),
    ]
