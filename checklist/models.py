from django.db import models

from equipos.models import TipoEquipo
from servicios.models import Servicio


class CategoriaSistema(models.TextChoices):
    """Agrupador por encima de SistemaChecklist: el checklist físico de Damol (MNT-F-001) se
    inspecciona en dos pasadas separadas —primero todo lo mecánico, luego todo lo eléctrico—
    más una tercera categoría de ítems generales que no son ni uno ni otro."""

    MECANICO = "mecanico", "Mecánico"
    ELECTRICO = "electrico", "Eléctrico"
    GENERALES = "generales", "Generales"


class SistemaChecklist(models.Model):
    """Plantilla: 'Polipasto', 'Trolley / Carro', 'Puente/Pluma', 'Componentes eléctricos del puente'..."""

    tipo_equipo = models.ForeignKey(
        TipoEquipo, related_name="sistemas_checklist", on_delete=models.CASCADE
    )
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaSistema.choices,
        default=CategoriaSistema.MECANICO,
        help_text="Agrupador para mostrar el checklist en pasadas (Mecánico → Eléctrico → Generales), como en el documento físico.",
    )
    nombre = models.CharField(max_length=150)
    orden = models.PositiveIntegerField(default=0)
    variantes_disponibles = models.JSONField(
        default=list,
        blank=True,
        help_text='Ej. ["Principal", "Auxiliar"] o ["Izquierdo", "Derecho"]. Vacío si no aplica.',
    )

    class Meta:
        ordering = ["tipo_equipo", "orden"]
        verbose_name = "Sistema de checklist"
        verbose_name_plural = "Sistemas de checklist"

    def __str__(self):
        return f"{self.nombre} ({self.tipo_equipo})"


class ItemChecklistPlantilla(models.Model):
    sistema = models.ForeignKey(SistemaChecklist, related_name="items", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10, blank=True)  # "1.1", "4.12"
    descripcion = models.CharField(max_length=255)
    orden = models.PositiveIntegerField(default=0)
    texto_plantilla = models.TextField(
        blank=True,
        help_text=(
            "Párrafo narrativo para el cuerpo del informe. Placeholders opcionales resueltos "
            "con str.format(): {nombre_item}, {variante}, {resultado_por_estado}."
        ),
    )

    class Meta:
        ordering = ["sistema", "orden"]
        verbose_name = "Ítem de checklist (plantilla)"
        verbose_name_plural = "Ítems de checklist (plantilla)"

    def __str__(self):
        return f"{self.codigo} {self.descripcion}".strip()


class EstadoItem(models.TextChoices):
    BUENO = "B", "Buen estado"
    REGULAR = "R", "Regular"
    MALO = "M", "Mal estado / alto riesgo"
    NO_APLICA = "NA", "No aplica"


# Descripción larga por estado, para mostrar como tooltip/ayuda junto al chip — no como el
# label del control, que se repetiría 40+ veces por checklist y se sentiría cargado.
DESCRIPCION_ESTADO_ITEM = {
    EstadoItem.BUENO: "Cumple su función, no requiere cambio en el corto plazo.",
    EstadoItem.REGULAR: "Cumple parcialmente, requiere pronto cambio o reparación.",
    EstadoItem.MALO: "No cumple, requiere cambio inmediato.",
    EstadoItem.NO_APLICA: "No aplica a este equipo.",
}

# Símbolo corto para el chip visual (el label del choice de arriba es el texto largo, correcto
# para el PDF y las tablas de revisión — pero repetido 40+ veces en un chip se ve cargado).
SIMBOLO_ESTADO_ITEM = {
    EstadoItem.BUENO: "B",
    EstadoItem.REGULAR: "R",
    EstadoItem.MALO: "M",
    EstadoItem.NO_APLICA: "N/A",
}

# Las 3 listas de arriba, ya combinadas en el orden de despliegue de los chips — lo que
# realmente necesita el template, para no tener que hacer 3 lookups por ítem ahí.
OPCIONES_ESTADO_CHIP = [
    (valor, SIMBOLO_ESTADO_ITEM[valor], DESCRIPCION_ESTADO_ITEM[valor])
    for valor in EstadoItem.values
]


class RespuestaChecklist(models.Model):
    servicio = models.ForeignKey(
        Servicio, related_name="respuestas_checklist", on_delete=models.CASCADE
    )
    item = models.ForeignKey(ItemChecklistPlantilla, related_name="respuestas", on_delete=models.PROTECT)
    variante = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=2, choices=EstadoItem.choices, null=True, blank=True)
    observacion = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["servicio", "item"]
        unique_together = ("servicio", "item", "variante")
        verbose_name = "Respuesta de checklist"
        verbose_name_plural = "Respuestas de checklist"

    def __str__(self):
        variante = f" ({self.variante})" if self.variante else ""
        return f"{self.item}{variante}: {self.estado}"


class FotoChecklist(models.Model):
    respuesta = models.ForeignKey(RespuestaChecklist, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="checklist_fotos/%Y/%m/")
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["respuesta", "orden"]

    def __str__(self):
        return self.descripcion or f"Foto {self.pk}"


class Hallazgo(models.Model):
    """Algo encontrado FUERA del checklist estándar (o, en un correctivo sin checklist
    completo, el contenido narrativo principal del informe). Independiente de
    RespuestaChecklist a propósito: debe poder registrarse con o sin checklist generado."""

    servicio = models.ForeignKey(Servicio, related_name="hallazgos", on_delete=models.CASCADE)
    sistema = models.ForeignKey(
        SistemaChecklist,
        related_name="hallazgos",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Sistema del equipo al que corresponde, si aplica (opcional).",
    )
    descripcion = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "Hallazgo importante"
        verbose_name_plural = "Hallazgos importantes"

    def __str__(self):
        return self.descripcion[:60]


class FotoHallazgo(models.Model):
    hallazgo = models.ForeignKey(Hallazgo, related_name="fotos", on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="hallazgos_fotos/%Y/%m/")
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["hallazgo", "orden"]

    def __str__(self):
        return self.descripcion or f"Foto {self.pk}"
