# Generated by Django 4.2.10 on 2024-03-03 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_project_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]
