from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.db import models


class NormaAplicable(models.Model):
    """Catálogo reutilizable de normas citadas en los informes (ANSI/ASME B30.16, CMAA 70, etc.)."""

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Norma aplicable"
        verbose_name_plural = "Normas aplicables"

    def __str__(self):
        return self.nombre


class EquipoMedicion(models.Model):
    """Instrumento de medición de Damol (multímetro, megóhmetro, pinza amperimétrica...)."""

    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    # Es un FileField "raw" para Cloudinary (documento, no imagen) — clase de storage propia.
    certificado_calibracion = models.FileField(
        upload_to="certificados_equipos/", blank=True, null=True, storage=RawMediaCloudinaryStorage()
    )
    fecha_calibracion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Equipo de medición"
        verbose_name_plural = "Equipos de medición"

    def __str__(self):
        return f"{self.nombre} ({self.marca} {self.modelo})".strip()
