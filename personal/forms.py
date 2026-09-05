from django.forms import inlineformset_factory

from servicios.models import Servicio

from .models import MaterialHerramienta, PersonalEjecutor

PersonalEjecutorFormSet = inlineformset_factory(
    Servicio,
    PersonalEjecutor,
    fields=["tecnico", "rol", "firma"],
    extra=1,
    can_delete=True,
)

# Variante liviana para asignar cuadrilla desde la cotización: sin firma, que se recoge en
# ejecución/entrega, no al cotizar.
PersonalEjecutorAsignacionFormSet = inlineformset_factory(
    Servicio,
    PersonalEjecutor,
    fields=["tecnico", "rol"],
    extra=1,
    can_delete=True,
)

MaterialHerramientaFormSet = inlineformset_factory(
    Servicio,
    MaterialHerramienta,
    fields=["item", "descripcion", "marca", "cantidad", "unidad"],
    extra=1,
    can_delete=True,
)
