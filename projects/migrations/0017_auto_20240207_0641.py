# Generated by Django 3.2.3 on 2024-02-07 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_alter_answer_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='projects',
            name='quotted_hours',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='task',
            name='quotted_hours',
            field=models.IntegerField(default=0),
        ),
    ]
