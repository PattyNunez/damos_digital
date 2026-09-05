from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.db import models

from servicios.models import Servicio


class Tecnico(models.Model):
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    dni = models.CharField(max_length=15, unique=True)
    cargo_habitual = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"


class PersonalEjecutor(models.Model):
    """Técnico asignado a UN servicio, con su rol y firma en ese servicio en particular."""

    servicio = models.ForeignKey(Servicio, related_name="personal_ejecutor", on_delete=models.CASCADE)
    tecnico = models.ForeignKey(Tecnico, related_name="participaciones", on_delete=models.PROTECT)
    rol = models.CharField(max_length=100)  # "Supervisor Operativo", "Técnico Electricista"...
    firma = models.ImageField(upload_to="firmas/", null=True, blank=True)

    class Meta:
        ordering = ["servicio", "id"]
        unique_together = ("servicio", "tecnico")
        verbose_name = "Personal ejecutor"
        verbose_name_plural = "Personal ejecutor"

    def __str__(self):
        return f"{self.tecnico} - {self.rol} ({self.servicio.codigo})"


class MaterialHerramienta(models.Model):
    servicio = models.ForeignKey(
        Servicio, related_name="materiales_herramientas", on_delete=models.CASCADE
    )
    item = models.PositiveIntegerField()
    descripcion = models.CharField(max_length=255)
    marca = models.CharField(max_length=100, blank=True)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unidad = models.CharField(max_length=30, default="Und")

    class Meta:
        ordering = ["servicio", "item"]
        verbose_name = "Material / herramienta"
        verbose_name_plural = "Materiales y herramientas"

    def __str__(self):
        return f"{self.descripcion} ({self.cantidad} {self.unidad})"


class CalificacionTecnico(models.Model):
    """Certificaciones vigentes del técnico (izaje, trabajos en altura, etc.) -> anexo del informe."""

    tecnico = models.ForeignKey(Tecnico, related_name="calificaciones", on_delete=models.CASCADE)
    nombre_certificacion = models.CharField(max_length=150)
    # Es un FileField "raw" para Cloudinary (documento, no imagen) — clase de storage propia.
    archivo = models.FileField(upload_to="certificaciones_tecnicos/", storage=RawMediaCloudinaryStorage())
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["tecnico", "-fecha_emision"]

    def __str__(self):
        return f"{self.nombre_certificacion} - {self.tecnico}"
