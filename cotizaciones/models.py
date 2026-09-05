from decimal import Decimal

from django.db import models


class ItemLineaBase(models.Model):
    """Campos comunes a las 4 secciones de línea del calculador."""

    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["orden", "id"]

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario


class DetalleCotizacion(models.Model):
    """Datos del calculador de costos (1:1 con Servicio), mismo patrón que FichaServicio."""

    servicio = models.OneToOneField(
        "servicios.Servicio", related_name="detalle_cotizacion", on_delete=models.CASCADE
    )

    porcentaje_indirectos = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    porcentaje_utilidad_servicio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    porcentaje_utilidad_repuestos = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Rollups calculados por recalcular(). No se editan a mano.
    subtotal_mano_obra = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    subtotal_logistica = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    subtotal_equipos = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    subtotal_materiales = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    monto_indirectos = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    monto_utilidad_servicio = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    monto_utilidad_repuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    subtotal_servicio = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    subtotal_repuestos = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    class Meta:
        verbose_name = "Detalle de cotización"
        verbose_name_plural = "Detalles de cotización"

    def __str__(self):
        return f"Detalle de cotización de {self.servicio.codigo}"

    def recalcular(self):
        """Recalcula los rollups de esta cotización y actualiza Servicio.subtotal/monto_igv/monto_total.

        Nota de negocio A VALIDAR CON DAMOL: los indirectos se calculan solo sobre la parte de
        servicio (mano de obra + logística + equipos), no sobre materiales. Es un supuesto
        razonable (el gasto administrativo se asocia a la gestión del trabajo, no al repuesto
        que se compra y revende) pero no confirmado todavía con una cotización real de Damol.
        """
        cero = Decimal("0")
        self.subtotal_mano_obra = sum((i.subtotal for i in self.items_mano_obra.all()), cero)
        self.subtotal_logistica = sum((i.subtotal for i in self.items_logistica.all()), cero)
        self.subtotal_equipos = sum((i.subtotal for i in self.items_equipo.all()), cero)
        self.subtotal_materiales = sum((i.subtotal for i in self.items_material.all()), cero)

        subtotal_directo_servicio = self.subtotal_mano_obra + self.subtotal_logistica + self.subtotal_equipos
        self.monto_indirectos = round(subtotal_directo_servicio * self.porcentaje_indirectos / 100, 2)
        base_servicio = subtotal_directo_servicio + self.monto_indirectos
        self.monto_utilidad_servicio = round(base_servicio * self.porcentaje_utilidad_servicio / 100, 2)
        self.subtotal_servicio = base_servicio + self.monto_utilidad_servicio

        self.monto_utilidad_repuestos = round(self.subtotal_materiales * self.porcentaje_utilidad_repuestos / 100, 2)
        self.subtotal_repuestos = self.subtotal_materiales + self.monto_utilidad_repuestos

        self.save()

        servicio = self.servicio
        servicio.subtotal = self.subtotal_servicio + self.subtotal_repuestos
        servicio.monto_igv = round(servicio.subtotal * servicio.porcentaje_igv / 100, 2)
        servicio.monto_total = servicio.subtotal + servicio.monto_igv
        servicio.save(update_fields=["subtotal", "monto_igv", "monto_total"])


class ItemManoObra(ItemLineaBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_mano_obra", on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, help_text="Rol/cargo, ej. 'Técnico especialista'.")

    class Meta(ItemLineaBase.Meta):
        verbose_name = "Ítem de mano de obra"
        verbose_name_plural = "Ítems de mano de obra"

    def __str__(self):
        return self.descripcion


class ItemLogistica(ItemLineaBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_logistica", on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, help_text="Ej. 'Pasaje aéreo Lima-Cusco', 'Hospedaje 3 noches'.")

    class Meta(ItemLineaBase.Meta):
        verbose_name = "Ítem de logística"
        verbose_name_plural = "Ítems de logística"

    def __str__(self):
        return self.descripcion


class ItemEquipo(ItemLineaBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_equipo", on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=255, help_text="Ej. 'Alquiler de grúa telescópica'.")

    class Meta(ItemLineaBase.Meta):
        verbose_name = "Ítem de equipo"
        verbose_name_plural = "Ítems de equipos"

    def __str__(self):
        return self.descripcion


class ItemMaterial(ItemLineaBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_material", on_delete=models.CASCADE)
    producto = models.ForeignKey(
        "inventario.Producto", related_name="items_cotizacion", on_delete=models.PROTECT
    )

    class Meta(ItemLineaBase.Meta):
        verbose_name = "Ítem de material"
        verbose_name_plural = "Ítems de materiales"

    def __str__(self):
        return f"{self.producto.codigo} x{self.cantidad}"


class ItemTextoBase(models.Model):
    """Campos comunes a las secciones cualitativas de la propuesta (alcance, exclusiones,
    provisiones). El orden se reordena con botones ▲▼ en el formulario, no tipeando un número."""

    texto = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["orden", "id"]

    def __str__(self):
        return self.texto[:60]


class ItemAlcance(ItemTextoBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_alcance", on_delete=models.CASCADE)

    class Meta(ItemTextoBase.Meta):
        verbose_name = "Ítem de alcance"
        verbose_name_plural = "Ítems de alcance"


class ItemExclusion(ItemTextoBase):
    detalle = models.ForeignKey(DetalleCotizacion, related_name="items_exclusion", on_delete=models.CASCADE)

    class Meta(ItemTextoBase.Meta):
        verbose_name = "Ítem de exclusión"
        verbose_name_plural = "Ítems de exclusión"


class ItemProvisionCliente(ItemTextoBase):
    detalle = models.ForeignKey(
        DetalleCotizacion, related_name="items_provision_cliente", on_delete=models.CASCADE
    )

    class Meta(ItemTextoBase.Meta):
        verbose_name = "Ítem de provisión del cliente"
        verbose_name_plural = "Ítems de provisión del cliente"


class ItemProvisionDamol(ItemTextoBase):
    detalle = models.ForeignKey(
        DetalleCotizacion, related_name="items_provision_damol", on_delete=models.CASCADE
    )

    class Meta(ItemTextoBase.Meta):
        verbose_name = "Ítem de provisión de Damol"
        verbose_name_plural = "Ítems de provisión de Damol"


class TipoItemCatalogo(models.TextChoices):
    """Las 7 categorías de texto libre del formulario que ahora tienen catálogo reutilizable
    (mano de obra/logística/equipos del calculador + alcance/exclusiones/provisiones) —
    deliberadamente NO se tocó el tipo de campo (descripcion/texto siguen siendo CharField, sin
    migración de datos) para no arriesgar nada a horas de la presentación; el catálogo solo
    alimenta sugerencias en el combobox por encima."""

    MANO_OBRA = "mano_obra", "Mano de obra"
    LOGISTICA = "logistica", "Logística"
    EQUIPO = "equipo", "Equipos (alquiler)"
    ALCANCE = "alcance", "Alcance del servicio"
    EXCLUSION = "exclusion", "Exclusiones"
    PROVISION_CLIENTE = "provision_cliente", "Provisiones del cliente"
    PROVISION_DAMOL = "provision_damol", "Provisiones de Damol"


class ItemCatalogo(models.Model):
    """Catálogo reutilizable de textos frecuentes por categoría — crece solo con el uso real:
    cada vez que alguien usa '+ Nuevo'/'+ Agregar nueva' en una cotización, el texto queda acá
    para sugerirse en cotizaciones futuras."""

    tipo = models.CharField(max_length=30, choices=TipoItemCatalogo.choices)
    texto = models.CharField(max_length=255)

    class Meta:
        unique_together = ("tipo", "texto")
        ordering = ["tipo", "texto"]
        verbose_name = "Ítem de catálogo"
        verbose_name_plural = "Ítems de catálogo"

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.texto}"
