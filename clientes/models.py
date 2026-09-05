from django.db import models


class Cliente(models.Model):
    razon_social = models.CharField(max_length=255)
    codigo_corto = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código corto usado en los correlativos de servicio, ej. VOLCAN.",
    )
    ruc = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    contacto_nombre = models.CharField(max_length=150, blank=True)
    contacto_telefono = models.CharField(max_length=30, blank=True)
    contacto_email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="clientes_logos/", blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social

    def save(self, *args, **kwargs):
        self.codigo_corto = self.codigo_corto.upper()
        super().save(*args, **kwargs)


class Ubicacion(models.Model):
    cliente = models.ForeignKey(Cliente, related_name="ubicaciones", on_delete=models.PROTECT)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["cliente", "nombre"]
        unique_together = ("cliente", "nombre")

    def __str__(self):
        return f"{self.nombre} ({self.cliente.codigo_corto})"
