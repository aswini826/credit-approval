# Generated by Django 5.0.2 on 2024-02-27 03:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit_app', '0002_alter_user_monthly_salary'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loan',
            name='user',
        ),
    ]
