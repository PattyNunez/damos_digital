from django import forms
from django.core.validators import RegexValidator
from django.forms import inlineformset_factory

from .models import Cliente, Ubicacion

validar_ruc = RegexValidator(
    regex=r"^(10|15|16|17|20)\d{9}$",
    message="El RUC debe tener 11 dígitos y empezar con 10, 15, 16, 17 o 20.",
)


class ClienteForm(forms.ModelForm):
    ruc = forms.CharField(required=False, validators=[validar_ruc])

    class Meta:
        model = Cliente
        fields = [
            "razon_social",
            "codigo_corto",
            "ruc",
            "direccion",
            "contacto_nombre",
            "contacto_telefono",
            "contacto_email",
            "logo",
        ]
        widgets = {
            "razon_social": forms.TextInput(),
            "codigo_corto": forms.TextInput(),
            "direccion": forms.TextInput(),
            "contacto_nombre": forms.TextInput(),
            "contacto_telefono": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.servicios.exists():
            self.fields["codigo_corto"].disabled = True


UbicacionFormSet = inlineformset_factory(
    Cliente,
    Ubicacion,
    fields=["nombre", "direccion"],
    extra=1,
    can_delete=True,
)


class ImportarClientesForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (.xlsx)")
