# Generated by Django 5.1.3 on 2024-12-18 12:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='investmentplan',
            name='monthly_profit',
        ),
        migrations.RemoveField(
            model_name='investmentplan',
            name='weekly_profit',
        ),
    ]