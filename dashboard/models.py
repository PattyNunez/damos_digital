from django.db import models


class ConfiguracionAlertas(models.Model):
    """Fila única (singleton) con los umbrales de las alertas automáticas del dashboard/kanban.

    Los valores de partida (5 y 7 días) son una propuesta a validar con Damol más adelante,
    no un acuerdo confirmado con ellos — por eso viven aquí como configurables desde el admin
    en vez de quedar fijos en código."""

    dias_alerta_cotizado = models.PositiveIntegerField(
        default=5,
        verbose_name="Días para alertar una cotización sin aprobar",
        help_text="Si un servicio lleva más de este número de días en estado 'Cotizado', se marca en alerta.",
    )
    dias_alerta_ejecucion = models.PositiveIntegerField(
        default=7,
        verbose_name="Días para alertar un trabajo atrasado",
        help_text="Si un servicio lleva más de este número de días en estado 'En ejecución', se marca en alerta.",
    )

    class Meta:
        verbose_name = "Configuración de alertas"
        verbose_name_plural = "Configuración de alertas"

    def __str__(self):
        return "Configuración de alertas"

    def save(self, *args, **kwargs):
        self.pk = 1  # fuerza singleton: siempre se sobreescribe la misma fila
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # no se permite borrar la única configuración

    @classmethod
    def cargar(cls):
        objeto, _ = cls.objects.get_or_create(pk=1)
        return objeto
