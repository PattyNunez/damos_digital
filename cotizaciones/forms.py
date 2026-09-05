from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory

from clientes.forms import validar_ruc
from clientes.models import Cliente, Ubicacion
from equipos.models import Equipo
from inventario.models import Producto
from personal.models import PersonalEjecutor, Tecnico
from servicios.models import Servicio, TipoServicio

from .models import (
    DetalleCotizacion,
    ItemAlcance,
    ItemEquipo,
    ItemExclusion,
    ItemLogistica,
    ItemManoObra,
    ItemMaterial,
    ItemProvisionCliente,
    ItemProvisionDamol,
)


class SelectorConClientePorOpcion(forms.Select):
    """Select (de Equipo o de Ubicación) que expone el cliente dueño por <option> vía
    data-cliente, para que el JS oculte/filtre las opciones que no son del cliente elegido —
    sin ida y vuelta al servidor. Mismo widget reutilizado para ambos campos."""

    def __init__(self, *args, clientes_por_opcion=None, **kwargs):
        self.clientes_por_opcion = clientes_por_opcion or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        pk = value.value if hasattr(value, "value") else value
        cliente_id = self.clientes_por_opcion.get(pk)
        if cliente_id is not None:
            option["attrs"]["data-cliente"] = str(cliente_id)
        return option


class ServicioCotizacionForm(forms.ModelForm):
    moneda = forms.ChoiceField(choices=[("PEN", "Soles (PEN)"), ("USD", "Dólares (USD)")], initial="PEN")

    class Meta:
        model = Servicio
        fields = [
            "tipo_servicio",
            "cliente",
            "equipo",
            "ubicacion",
            "servicio_origen",
            "orden_compra",
            "titulo",
            "elaborado_por",
            "moneda",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["servicio_origen"].queryset = Servicio.objects.filter(tipo_servicio=TipoServicio.PREVENTIVO)
        self.fields["servicio_origen"].required = False
        self.fields["servicio_origen"].label = "Preventivo de origen"

        clientes_por_equipo = dict(Equipo.objects.values_list("pk", "cliente_id"))
        widget_equipo = SelectorConClientePorOpcion(clientes_por_opcion=clientes_por_equipo)
        widget_equipo.choices = self.fields["equipo"].choices
        self.fields["equipo"].widget = widget_equipo

        clientes_por_ubicacion = dict(Ubicacion.objects.values_list("pk", "cliente_id"))
        widget_ubicacion = SelectorConClientePorOpcion(clientes_por_opcion=clientes_por_ubicacion)
        widget_ubicacion.choices = self.fields["ubicacion"].choices
        self.fields["ubicacion"].widget = widget_ubicacion


class ClienteRapidoForm(forms.ModelForm):
    """Creación mínima de Cliente desde el combobox "buscar o crear" de la cotización —
    no reemplaza el formulario completo de clientes/, solo cubre lo indispensable."""

    ruc = forms.CharField(required=False, validators=[validar_ruc])

    class Meta:
        model = Cliente
        fields = ["razon_social", "codigo_corto", "ruc"]


class EquipoRapidoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ["cliente", "tipo_equipo", "codigo_interno"]


class UbicacionRapidoForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ["cliente", "nombre", "direccion"]


class TecnicoRapidoForm(forms.ModelForm):
    class Meta:
        model = Tecnico
        fields = ["nombres", "apellidos", "dni"]


class ProductoRapidoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["codigo", "nombre", "precio_referencial", "moneda"]


class DetalleCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleCotizacion
        fields = ["porcentaje_indirectos", "porcentaje_utilidad_servicio", "porcentaje_utilidad_repuestos"]


ItemManoObraFormSet = inlineformset_factory(
    DetalleCotizacion,
    ItemManoObra,
    fields=["descripcion", "cantidad", "costo_unitario"],
    extra=1,
    can_delete=True,
)

ItemLogisticaFormSet = inlineformset_factory(
    DetalleCotizacion,
    ItemLogistica,
    fields=["descripcion", "cantidad", "costo_unitario"],
    extra=1,
    can_delete=True,
)

ItemEquipoFormSet = inlineformset_factory(
    DetalleCotizacion,
    ItemEquipo,
    fields=["descripcion", "cantidad", "costo_unitario"],
    extra=1,
    can_delete=True,
)


class SelectorProductoConPrecio(forms.Select):
    """Select de Producto que expone precio/moneda por <option> vía data-attrs, para que el
    JS precargue costo_unitario y avise si la moneda del producto difiere de la cotización."""

    def __init__(self, *args, precios=None, **kwargs):
        self.precios = precios or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        pk = value.value if hasattr(value, "value") else value
        datos = self.precios.get(pk)
        if datos:
            option["attrs"]["data-precio"] = str(datos[0])
            option["attrs"]["data-moneda"] = datos[1]
        return option


class ItemMaterialForm(forms.ModelForm):
    class Meta:
        model = ItemMaterial
        fields = ["producto", "cantidad", "costo_unitario"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        productos = Producto.objects.filter(activo=True)
        # Al editar una línea ya guardada cuyo producto se desactivó después, hay que seguir
        # incluyéndolo — si no, el <select> no podría mostrar ni validar el valor ya elegido.
        if self.instance and self.instance.pk and self.instance.producto_id:
            productos = Producto.objects.filter(Q(activo=True) | Q(pk=self.instance.producto_id))
        self.fields["producto"].queryset = productos
        precios = {p.pk: (p.precio_referencial, p.moneda) for p in productos}
        widget = SelectorProductoConPrecio(precios=precios)
        widget.choices = self.fields["producto"].choices
        self.fields["producto"].widget = widget


ItemMaterialFormSet = inlineformset_factory(
    DetalleCotizacion,
    ItemMaterial,
    form=ItemMaterialForm,
    fields=["producto", "cantidad", "costo_unitario"],
    extra=1,
    can_delete=True,
)


class ItemTextoForm(forms.ModelForm):
    """Base para las 4 secciones cualitativas: 'orden' viaja oculto, lo recalcula el JS
    de reordenar (▲▼) justo antes de enviar el formulario, no lo tipea la persona."""

    class Meta:
        fields = ["texto", "orden"]
        widgets = {
            "texto": forms.TextInput(),
            "orden": forms.HiddenInput(),
        }


def _formset_texto(modelo):
    class _Form(ItemTextoForm):
        class Meta(ItemTextoForm.Meta):
            model = modelo

    return inlineformset_factory(
        DetalleCotizacion, modelo, form=_Form, fields=["texto", "orden"], extra=1, can_delete=True
    )


ItemAlcanceFormSet = _formset_texto(ItemAlcance)
ItemExclusionFormSet = _formset_texto(ItemExclusion)
ItemProvisionClienteFormSet = _formset_texto(ItemProvisionCliente)
ItemProvisionDamolFormSet = _formset_texto(ItemProvisionDamol)
