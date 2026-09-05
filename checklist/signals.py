from django.db.models.signals import post_save
from django.dispatch import receiver

from servicios.models import Servicio, TipoServicio

from .models import ItemChecklistPlantilla, RespuestaChecklist


@receiver(post_save, sender=Servicio)
def _generar_checklist_desde_plantilla(sender, instance, created, **kwargs):
    """Al crear un Servicio PREVENTIVO, copia la plantilla de checklist (SistemaChecklist +
    ItemChecklistPlantilla) del TipoEquipo del equipo asociado a RespuestaChecklist,
    una fila vacía por ítem (o por ítem x variante, si el sistema define variantes).

    Un correctivo NO recibe el checklist completo: su contenido narrativo se apoya 100% en
    Hallazgo (independiente de RespuestaChecklist), no en revisar el equipo desde cero."""
    if not created or instance.tipo_servicio != TipoServicio.PREVENTIVO:
        return

    items = ItemChecklistPlantilla.objects.filter(
        sistema__tipo_equipo=instance.equipo.tipo_equipo
    ).select_related("sistema")

    respuestas = [
        RespuestaChecklist(servicio=instance, item=item, variante=variante)
        for item in items
        for variante in (item.sistema.variantes_disponibles or [""])
    ]

    RespuestaChecklist.objects.bulk_create(respuestas, ignore_conflicts=True)
