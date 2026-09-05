from django.db import models

from clientes.models import Cliente, Ubicacion


class TipoEquipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    # "Puente Grúa", "Grúa Pórtico", "Polipasto", "Grúa Pescante", "Monorriel", etc.

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    cliente = models.ForeignKey(Cliente, related_name="equipos", on_delete=models.PROTECT)
    tipo_equipo = models.ForeignKey(TipoEquipo, related_name="equipos", on_delete=models.PROTECT)
    ubicacion = models.ForeignKey(
        Ubicacion, related_name="equipos", null=True, blank=True, on_delete=models.SET_NULL
    )
    codigo_interno = models.CharField(max_length=50, blank=True, help_text="TAG del equipo.")
    marca_estructura = models.CharField(max_length=100, blank=True)
    marca_polipasto = models.CharField(max_length=100, blank=True)
    capacidad_ton = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    fecha_fabricacion = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to="equipos_fotos/", blank=True, null=True)
    foto_ubicacion = models.ImageField(upload_to="equipos_fotos/", blank=True, null=True)
    especificaciones = models.JSONField(
        default=dict,
        blank=True,
        help_text="Specs técnicas variables según tipo de equipo (span, voltajes, velocidades, etc.).",
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["cliente", "tipo_equipo", "codigo_interno"]

    def __str__(self):
        etiqueta = self.codigo_interno or self.modelo or str(self.tipo_equipo)
        return f"{self.tipo_equipo} {etiqueta} - {self.cliente.codigo_corto}"
