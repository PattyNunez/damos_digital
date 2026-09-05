from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.conf import settings
from django.db import models

from servicios.models import Servicio


class InformeGenerado(models.Model):
    servicio = models.OneToOneField(Servicio, related_name="informe", on_delete=models.CASCADE)
    numero_informe = models.CharField(max_length=50, blank=True)
    # PDF: es un FileField "raw" para Cloudinary, no un ImageField — necesita su propia clase de
    # storage (resource_type=raw); la clase por defecto del proyecto es para imágenes.
    archivo_pdf = models.FileField(upload_to="informes/%Y/%m/", storage=RawMediaCloudinaryStorage())
    # auto_now (no auto_now_add): al regenerar se reemplaza el archivo y se sube la versión,
    # así que la fecha debe reflejar la última generación, no la primera.
    generado_en = models.DateTimeField(auto_now=True)
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-generado_en"]

    def __str__(self):
        return self.numero_informe or f"Informe de {self.servicio.codigo}"


class ConfiguracionInforme(models.Model):
    """Fila única (pk=1 forzado) con datos fijos del informe, editables desde el admin y
    reutilizados en todos los PDF generados."""

    logo = models.ImageField(upload_to="config_informe/", blank=True, null=True)
    encabezado_codigo = models.CharField(max_length=30, default="JP-F-007")
    encabezado_version = models.CharField(max_length=10, default="04")
    encabezado_fecha_aprobacion = models.DateField(null=True, blank=True)
    normatividad_texto = models.TextField(blank=True)

    # Textos fijos reutilizados en toda propuesta comercial generada (mismo criterio que
    # normatividad_texto arriba: institucional, no varía por cotización individual).
    propuesta_intro_texto = models.TextField(
        blank=True,
        default=(
            "De nuestra consideración:\n\n"
            "Es un agrado saludarlos cordialmente. De acuerdo a sus requerimientos, presentamos "
            "nuestra propuesta técnico-económica para el desarrollo del servicio descrito en el "
            "presente documento, garantizando el cumplimiento de los estándares de seguridad y la "
            "normativa aplicable vigente en mantenimiento de equipos de izaje."
        ),
    )
    propuesta_validez_dias = models.PositiveIntegerField(default=30)
    propuesta_terminos_adicionales = models.TextField(
        blank=True, help_text="Cláusulas fijas adicionales, una por línea (forma de pago, plazo, etc.)."
    )

    class Meta:
        verbose_name = "Configuración del informe"
        verbose_name_plural = "Configuración del informe"

    def __str__(self):
        return "Configuración del informe"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class PropuestaComercial(models.Model):
    """PDF de propuesta comercial para el cliente (espejo de InformeGenerado): partidas
    redistribuidas sin exponer % de margen, alcance/exclusiones/provisiones, términos fijos."""

    servicio = models.OneToOneField(Servicio, related_name="propuesta_comercial", on_delete=models.CASCADE)
    archivo_pdf = models.FileField(upload_to="propuestas/%Y/%m/", storage=RawMediaCloudinaryStorage())
    generado_en = models.DateTimeField(auto_now=True)
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-generado_en"]

    def __str__(self):
        return f"Propuesta comercial de {self.servicio.codigo}"
