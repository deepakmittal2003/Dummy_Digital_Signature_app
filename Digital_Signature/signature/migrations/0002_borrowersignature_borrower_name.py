# Generated by Django 5.0.4 on 2024-07-01 10:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("signature", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="borrowersignature",
            name="borrower_name",
            field=models.CharField(default="Default Borrower", max_length=100),
        ),
    ]
