# Generated by Django 3.1 on 2020-12-28 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Block",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("index", models.IntegerField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("transactions", models.CharField(max_length=255)),
                ("proof", models.IntegerField()),
                ("previous_hash", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sender", models.CharField(max_length=255)),
                ("recipient", models.CharField(max_length=255)),
                ("amount", models.IntegerField()),
            ],
        ),
    ]
