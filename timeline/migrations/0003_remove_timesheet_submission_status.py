# Generated by Django 3.2.3 on 2021-07-01 21:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_auto_20210702_0235'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timesheet_submission',
            name='status',
        ),
    ]
