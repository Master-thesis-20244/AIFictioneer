# Generated by Django 5.0 on 2024-03-11 22:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AIFictioneer', '0002_alter_prompt_json_structure_example_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ontology',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('json_structure', models.JSONField()),
            ],
        ),
        migrations.RemoveField(
            model_name='prompt',
            name='json_structure_example',
        ),
        migrations.AlterField(
            model_name='prompt',
            name='ontology',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prompts', to='AIFictioneer.ontology'),
        ),
    ]
