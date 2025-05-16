from django.db import models


class GlobalNews(models.Model):
    class SevSeverityChoices(models.TextChoices):
        PRIMARY = "primary", "Primary"
        SECONDARY = "secondary", "Secondary"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        DANGER = "danger", "Danger"
        INFO = "info", "Info"
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержимое")
    severity = models.CharField(
        max_length=16,
        choices=SevSeverityChoices.choices,
        default=SevSeverityChoices.INFO,
        verbose_name="Важность",
        help_text="Уровень важности сообщения",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время истечения",
        help_text="Время, до которого будет отображаться сообщение",
    )

    class Meta:
        db_table = "global_news"
        verbose_name = "Глобальная новость"
        verbose_name_plural = "Глобальные новости"
        ordering = ["-created_at"]
