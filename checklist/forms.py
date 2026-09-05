import io

from django import forms
from django.core.files.base import ContentFile
from django.forms import inlineformset_factory, modelformset_factory
from PIL import Image

from servicios.models import Servicio

from .models import FotoChecklist, FotoHallazgo, Hallazgo, RespuestaChecklist, SistemaChecklist


def _convertir_a_jpeg_si_es_heic(archivo):
    """Los iPhone guardan fotos en HEIC/HEIF por defecto. Pillow ya sabe LEER ese formato
    (pillow-heif registrado en settings.py), pero los navegadores (salvo Safari) y el PDF del
    informe no pueden MOSTRAR un <img> en HEIC directamente — hay que convertir a JPEG al subir,
    no solo aceptar el archivo."""
    nombre = (archivo.name or "").lower()
    if not (nombre.endswith(".heic") or nombre.endswith(".heif")):
        return archivo
    imagen = Image.open(archivo)
    imagen = imagen.convert("RGB")
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", quality=90)
    nuevo_nombre = archivo.name.rsplit(".", 1)[0] + ".jpg"
    return ContentFile(buffer.getvalue(), name=nuevo_nombre)

RespuestaChecklistFormSet = modelformset_factory(
    RespuestaChecklist,
    fields=["estado", "observacion"],
    extra=0,
    widgets={"estado": forms.RadioSelect},
)


class FotoChecklistForm(forms.ModelForm):
    class Meta:
        model = FotoChecklist
        fields = ["imagen", "descripcion"]
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
        }

    def clean_imagen(self):
        return _convertir_a_jpeg_si_es_heic(self.cleaned_data["imagen"])


class HallazgoForm(forms.ModelForm):
    class Meta:
        model = Hallazgo
        fields = ["sistema", "descripcion"]

    def __init__(self, *args, tipo_equipo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tipo_equipo is not None:
            self.fields["sistema"].queryset = SistemaChecklist.objects.filter(tipo_equipo=tipo_equipo)


HallazgoFormSet = inlineformset_factory(
    Servicio,
    Hallazgo,
    form=HallazgoForm,
    fields=["sistema", "descripcion"],
    extra=1,
    can_delete=True,
)


class FotoHallazgoForm(forms.ModelForm):
    class Meta:
        model = FotoHallazgo
        fields = ["imagen", "descripcion"]
        widgets = {
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"}),
        }

    def clean_imagen(self):
        return _convertir_a_jpeg_si_es_heic(self.cleaned_data["imagen"])
