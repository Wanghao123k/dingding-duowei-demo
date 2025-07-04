# Generated by Django 5.2.3 on 2025-06-17 09:00

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="任务标题")),
                ("code", models.CharField(max_length=50, verbose_name="任务代码")),
                ("description", models.TextField(blank=True, verbose_name="任务描述")),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="创建时间"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "is_completed",
                    models.BooleanField(default=False, verbose_name="是否完成"),
                ),
            ],
            options={
                "verbose_name": "任务",
                "verbose_name_plural": "任务",
                "ordering": ["-created_at"],
            },
        ),
    ]
