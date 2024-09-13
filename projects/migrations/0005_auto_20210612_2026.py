# Generated by Django 3.2.3 on 2021-06-12 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_alter_milestone_start_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='milestone',
            old_name='start_date',
            new_name='created_date',
        ),
        migrations.AddField(
            model_name='milestone',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
