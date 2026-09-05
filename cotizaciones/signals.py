from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ItemEquipo, ItemLogistica, ItemManoObra, ItemMaterial


@receiver([post_save, post_delete], sender=ItemManoObra)
@receiver([post_save, post_delete], sender=ItemLogistica)
@receiver([post_save, post_delete], sender=ItemEquipo)
@receiver([post_save, post_delete], sender=ItemMaterial)
def _recalcular_detalle_cotizacion(sender, instance, **kwargs):
    instance.detalle.recalcular()
