from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from catalogos.models import EquipoMedicion, NormaAplicable
from clientes.models import Cliente, Ubicacion
from equipos.models import Equipo


class TipoServicio(models.TextChoices):
    PREVENTIVO = "preventivo", "Preventivo"
    CORRECTIVO = "correctivo", "Correctivo"


# Objetivo/Antecedentes son prácticamente el mismo texto estándar en todos los servicios de un
# mismo tipo — no tiene sentido pedirle al técnico que lo escriba en campo cada vez. Se usan
# como precarga editable en el formulario y como respaldo al generar el informe si quedó vacío.
TEXTOS_ESTANDAR_OBJETIVO = {
    TipoServicio.PREVENTIVO: (
        "Realizar el mantenimiento preventivo para asegurar la operatividad del equipo de izaje, "
        "conforme al plan de mantenimiento programado."
    ),
    TipoServicio.CORRECTIVO: (
        "Realizar el diagnóstico y corrección de la falla reportada en el equipo de izaje, "
        "restableciendo su operatividad segura."
    ),
}

TEXTOS_ESTANDAR_ANTECEDENTES = {
    TipoServicio.PREVENTIVO: (
        "El equipo cuenta con un plan de mantenimiento preventivo periódico, orientado a "
        "preservar su condición operativa y prevenir fallas antes de que ocurran."
    ),
    TipoServicio.CORRECTIVO: (
        "Se reportó una falla o condición anómala en el equipo que requiere intervención "
        "correctiva para restablecer su operatividad segura."
    ),
}


TIPO_SERVICIO_PREFIJOS = {
    TipoServicio.PREVENTIVO: "PREV",
    TipoServicio.CORRECTIVO: "CORR",
}


class EstadoServicio(models.TextChoices):
    COTIZADO = "cotizado", "Cotizado"
    APROBADO = "aprobado", "Aprobado"
    EN_EJECUCION = "en_ejecucion", "En ejecución"
    ENTREGADO = "entregado", "Entregado"


ESTADO_PREFIJOS = {
    EstadoServicio.COTIZADO: "COT",
    EstadoServicio.APROBADO: "SERV",
    EstadoServicio.EN_EJECUCION: "SERV",
    EstadoServicio.ENTREGADO: "SERV",
}


class SecuenciaCorrelativo(models.Model):
    """Contador atómico: una fila por combinación (tipo_servicio, cliente, año)."""

    tipo_servicio = models.CharField(max_length=20, choices=TipoServicio.choices)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    anio = models.PositiveIntegerField()
    ultimo_valor = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("tipo_servicio", "cliente", "anio")
        verbose_name = "Secuencia de correlativo"
        verbose_name_plural = "Secuencias de correlativo"

    def __str__(self):
        return f"{self.tipo_servicio}-{self.cliente.codigo_corto}-{self.anio}: {self.ultimo_valor}"


class Servicio(models.Model):
    tipo_servicio = models.CharField(max_length=20, choices=TipoServicio.choices)
    cliente = models.ForeignKey(Cliente, related_name="servicios", on_delete=models.PROTECT)
    equipo = models.ForeignKey(Equipo, related_name="servicios", on_delete=models.PROTECT)
    ubicacion = models.ForeignKey(
        Ubicacion, related_name="servicios", null=True, blank=True, on_delete=models.SET_NULL
    )
    servicio_origen = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="correctivos_generados",
        on_delete=models.SET_NULL,
        help_text="Preventivo del que se originó este correctivo, si aplica.",
    )

    anio = models.PositiveIntegerField(editable=False)
    correlativo = models.PositiveIntegerField(editable=False)
    codigo = models.CharField(max_length=60, unique=True, editable=False)

    estado = models.CharField(
        max_length=20, choices=EstadoServicio.choices, default=EstadoServicio.COTIZADO
    )
    orden_compra = models.CharField(max_length=50, blank=True)
    titulo = models.CharField(max_length=255, blank=True)
    elaborado_por = models.CharField(
        max_length=150,
        blank=True,
        help_text="Nombre de quien elabora el informe, tal como debe aparecer en la portada.",
    )

    # Montos calculados desde DetalleCotizacion.recalcular() (app cotizaciones). No editables a mano.
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    porcentaje_igv = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    monto_igv = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    moneda = models.CharField(max_length=3, default="PEN")

    fecha_cotizacion = models.DateField(null=True, blank=True)
    fecha_aprobacion = models.DateField(null=True, blank=True)
    fecha_ejecucion_inicio = models.DateField(null=True, blank=True)
    fecha_ejecucion_fin = models.DateField(null=True, blank=True)
    fecha_entrega = models.DateField(null=True, blank=True)

    normas_aplicables = models.ManyToManyField(NormaAplicable, blank=True, related_name="servicios")
    equipos_medicion_usados = models.ManyToManyField(
        EquipoMedicion, blank=True, related_name="servicios"
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-anio", "-correlativo"]

    def __str__(self):
        return self.codigo

    def asignar_correlativo(self):
        """Genera año/correlativo de forma atómica. Solo se llama una vez, al crear."""
        with transaction.atomic():
            secuencia, _ = SecuenciaCorrelativo.objects.select_for_update().get_or_create(
                tipo_servicio=self.tipo_servicio,
                cliente=self.cliente,
                anio=self.anio,
            )
            secuencia.ultimo_valor += 1
            secuencia.save(update_fields=["ultimo_valor"])
            self.correlativo = secuencia.ultimo_valor

    def actualizar_codigo(self):
        """Recalcula el código visible. El prefijo COT/SERV cambia con el estado,
        pero (tipo_servicio, cliente, año, correlativo) permanecen fijos de por vida."""
        self.codigo = "-".join(
            [
                ESTADO_PREFIJOS[self.estado],
                TIPO_SERVICIO_PREFIJOS[self.tipo_servicio],
                str(self.anio),
                self.cliente.codigo_corto,
                f"{self.correlativo:03d}",
            ]
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.anio:
                self.anio = (self.fecha_cotizacion or timezone.localdate()).year
            self.asignar_correlativo()
        self.actualizar_codigo()
        super().save(*args, **kwargs)

    @property
    def informe_disponible(self):
        """Gate para 'Generar informe': antes de la visita no hay nada real que reportar.
        Preventivo depende del checklist (al menos 1 ítem con estado guardado — el umbral
        más simple posible, a endurecer más adelante si hace falta con uso real). Correctivo
        no genera checklist por diseño (ver checklist/signals.py), así que depende de que
        haya al menos un Hallazgo registrado — es donde ese tipo documenta lo encontrado y
        resuelto. Usa related_names (respuestas_checklist / hallazgos) en vez de importar los
        modelos de la app checklist, para no crear un import circular (checklist/models.py
        ya importa Servicio)."""
        if self.tipo_servicio == TipoServicio.CORRECTIVO:
            return self.hallazgos.exists()
        return self.respuestas_checklist.filter(estado__isnull=False).exists()

    @property
    def mensaje_informe_no_disponible(self):
        if self.tipo_servicio == TipoServicio.CORRECTIVO:
            return "Registra al menos un hallazgo de la visita para poder generar el informe."
        return "Completa el checklist de la visita para poder generar el informe."


class HistorialEstadoServicio(models.Model):
    """Una fila por cada cambio de estado. Se crea automáticamente vía signal (ver signals.py)."""

    servicio = models.ForeignKey(Servicio, related_name="historial_estados", on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=EstadoServicio.choices)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["servicio", "fecha_cambio"]
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"

    def __str__(self):
        return f"{self.servicio.codigo}: {self.estado} ({self.fecha_cambio:%Y-%m-%d %H:%M})"


class FichaServicio(models.Model):
    """Datos de campo (1:1 con Servicio): datos generales + narrativa del informe."""

    servicio = models.OneToOneField(Servicio, related_name="ficha", on_delete=models.CASCADE)
    fecha_servicio = models.DateField(null=True, blank=True)
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)
    condiciones_ambientales = models.TextField(blank=True)
    especificaciones_polipasto = models.JSONField(
        default=dict, blank=True, help_text="Specs del polipasto (clasificación, velocidades, voltajes, etc.)."
    )
    especificaciones_trolley = models.JSONField(
        default=dict, blank=True, help_text="Specs del trolley (span, diámetro de cable, torsión, etc.)."
    )
    objetivo = models.TextField(blank=True)
    antecedentes = models.TextField(blank=True)
    trabajos_previos = models.TextField(blank=True)

    def __str__(self):
        return f"Ficha de {self.servicio.codigo}"


class Observacion(models.Model):
    servicio = models.ForeignKey(Servicio, related_name="observaciones", on_delete=models.CASCADE)
    texto = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.texto[:60]


class Recomendacion(models.Model):
    servicio = models.ForeignKey(Servicio, related_name="recomendaciones", on_delete=models.CASCADE)
    texto = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.texto[:60]


class Conclusion(models.Model):
    servicio = models.ForeignKey(Servicio, related_name="conclusiones", on_delete=models.CASCADE)
    texto = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.texto[:60]


class FirmaAprobacion(models.Model):
    """V°B° Damol / V°B° Cliente al pie del formulario (distinto de la firma de cada técnico)."""

    servicio = models.OneToOneField(Servicio, related_name="firma_aprobacion", on_delete=models.CASCADE)
    nombre_damol = models.CharField(max_length=150, blank=True)
    fecha_damol = models.DateField(null=True, blank=True)
    firma_damol = models.ImageField(upload_to="firmas/", null=True, blank=True)
    nombre_cliente = models.CharField(max_length=150, blank=True)
    fecha_cliente = models.DateField(null=True, blank=True)
    firma_cliente = models.ImageField(upload_to="firmas/", null=True, blank=True)

    def __str__(self):
        return f"Firmas de {self.servicio.codigo}"
