from django.contrib import admin

from .models import DataFile


@admin.register(DataFile)
class DataFileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "file_size",
        "record_count",
        "status",
        "uploaded_at",
        "processed_at",
    )
    list_filter = ("status", "uploaded_at")
    search_fields = ("name", "user__email")
    readonly_fields = ("uploaded_at", "processed_at")
