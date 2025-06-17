from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'is_completed', 'created_at', 'updated_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['code', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_completed']
    ordering = ['-created_at']
