# Generated by Django 3.2.3 on 2024-02-07 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Employee', '0006_rename_group_customemployeedetails_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customemployeedetails',
            name='reporting_to',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
