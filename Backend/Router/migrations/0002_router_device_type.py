# Generated by Django 5.2.4 on 2025-07-19 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Router', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='router',
            name='device_type',
            field=models.CharField(default='juniper', max_length=50),
        ),
    ]
