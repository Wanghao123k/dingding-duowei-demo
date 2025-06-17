from django.db import models
from django.utils import timezone


class Task(models.Model):
    title = models.CharField(max_length=200, verbose_name="任务标题")
    code = models.CharField(max_length=50, verbose_name="任务代码")
    description = models.TextField(blank=True, verbose_name="任务描述")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.title}"
