from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DataFile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="data_files",
        verbose_name=_("User"),
    )
    name = models.CharField(_("File Name"), max_length=255)
    file = models.FileField(_("File"), upload_to='uploads/%Y/%m/%d/')
    file_size = models.IntegerField(_("File Size (bytes)"))
    record_count = models.IntegerField(_("Record Count"), default=0)
    columns = models.JSONField(_("Columns"), default=list, blank=True)
    data = models.JSONField(_("Data"), default=list, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ('uploaded', 'Uploaded'),
            ('processing', 'Processing'),
            ('processed', 'Processed'),
            ('error', 'Error'),
        ],
        default='uploaded'
    )
    error_message = models.TextField(_("Error Message"), blank=True)
    uploaded_at = models.DateTimeField(_("Uploaded At"), auto_now_add=True)
    processed_at = models.DateTimeField(_("Processed At"), null=True, blank=True)

    class Meta:
        verbose_name_plural = "Data Files"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.record_count} records)"
