from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import HistorialEstadoServicio, Servicio


@receiver(pre_save, sender=Servicio)
def _cachear_estado_anterior(sender, instance, **kwargs):
    """Guarda el estado que tenía en BD antes de este save(), para poder compararlo después."""
    if instance.pk:
        estado_anterior = (
            Servicio.objects.filter(pk=instance.pk).values_list("estado", flat=True).first()
        )
    else:
        estado_anterior = None
    instance._estado_anterior = estado_anterior


@receiver(post_save, sender=Servicio)
def _registrar_cambio_estado(sender, instance, created, **kwargs):
    """Crea automáticamente una fila de historial al crear el servicio o cuando cambia el estado."""
    estado_anterior = getattr(instance, "_estado_anterior", None)
    if created or estado_anterior != instance.estado:
        HistorialEstadoServicio.objects.create(servicio=instance, estado=instance.estado)
