from django.db import models


class Moneda(models.TextChoices):
    PEN = "PEN", "Soles (PEN)"
    USD = "USD", "Dólares (USD)"


class Proveedor(models.Model):
    razon_social = models.CharField(max_length=255)
    ruc = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    contacto_nombre = models.CharField(max_length=150, blank=True)
    contacto_telefono = models.CharField(max_length=30, blank=True)
    contacto_email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    unidad_medida = models.CharField(max_length=20, blank=True)
    precio_referencial = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=Moneda.choices, default=Moneda.PEN)
    proveedor_principal = models.ForeignKey(
        Proveedor,
        related_name="productos",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["categoria", "nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)
