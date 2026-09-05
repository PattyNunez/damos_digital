from django.db import models

from servicios.models import Servicio


class GrupoMedicion(models.Model):
    """Una tabla de mediciones dentro de un servicio: 'Megado de motores', 'Medida de frenos',
    'Medición de corriente'... Filas y columnas son 100% configurables, no hardcodeadas."""

    servicio = models.ForeignKey(Servicio, related_name="grupos_medicion", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    unidad = models.CharField(max_length=20, blank=True)  # "MΩ", "Ω", "A", "mm"
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["servicio", "orden"]
        verbose_name = "Grupo de mediciones"
        verbose_name_plural = "Grupos de mediciones"

    def __str__(self):
        return f"{self.nombre} ({self.servicio.codigo})"


class ColumnaMedicion(models.Model):
    grupo = models.ForeignKey(GrupoMedicion, related_name="columnas", on_delete=models.CASCADE)
    etiqueta = models.CharField(max_length=100)  # "Polipasto Principal", "Trolley Motor 1"...
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["grupo", "orden"]

    def __str__(self):
        return self.etiqueta


class FilaMedicion(models.Model):
    grupo = models.ForeignKey(GrupoMedicion, related_name="filas", on_delete=models.CASCADE)
    etiqueta = models.CharField(max_length=100)  # "V1+T", "Subida", "IZAJE"...
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["grupo", "orden"]

    def __str__(self):
        return self.etiqueta


class ValorMedicion(models.Model):
    fila = models.ForeignKey(FilaMedicion, related_name="valores", on_delete=models.CASCADE)
    columna = models.ForeignKey(ColumnaMedicion, related_name="valores", on_delete=models.CASCADE)
    valor = models.CharField(max_length=50, blank=True)  # texto libre: ">550", "---", "15.6", etc.

    class Meta:
        unique_together = ("fila", "columna")

    def __str__(self):
        return f"{self.fila} x {self.columna} = {self.valor}"
