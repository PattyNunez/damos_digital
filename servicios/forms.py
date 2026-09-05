from django.forms import inlineformset_factory, modelform_factory

from .models import Conclusion, FichaServicio, Observacion, Recomendacion, Servicio

FichaServicioForm = modelform_factory(
    FichaServicio,
    fields=[
        "fecha_servicio",
        "hora_entrada",
        "hora_salida",
        "condiciones_ambientales",
        "objetivo",
        "antecedentes",
        "trabajos_previos",
    ],
)

ObservacionFormSet = inlineformset_factory(
    Servicio, Observacion, fields=["texto", "orden"], extra=1, can_delete=True
)

RecomendacionFormSet = inlineformset_factory(
    Servicio, Recomendacion, fields=["texto", "orden"], extra=1, can_delete=True
)

ConclusionFormSet = inlineformset_factory(
    Servicio, Conclusion, fields=["texto", "orden"], extra=1, can_delete=True
)
