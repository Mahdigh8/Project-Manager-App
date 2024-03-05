# Generated by Django 4.2.10 on 2024-03-05 09:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_project_deadline'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('To-Do', 'TODO'), ('In Progress', 'PROG'), ('Done', 'DONE')], default='TODO', max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='core.teammember')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.teammember')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='core.project')),
            ],
        ),
    ]
