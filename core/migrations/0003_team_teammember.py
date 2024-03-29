# Generated by Django 4.2.10 on 2024-02-28 09:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_customuser_options_alter_customuser_managers_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('public_edit', models.CharField(choices=[('ALL', 'All team members'), ('ADMIN', 'Only team admins')], default='ALL', max_length=10)),
                ('privacy_edit', models.CharField(choices=[('ALL', 'All team members'), ('ADMIN', 'Only team admins')], default='ALL', max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_admin', models.BooleanField(default=False)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member', to='core.team')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'team')},
            },
        ),
    ]
