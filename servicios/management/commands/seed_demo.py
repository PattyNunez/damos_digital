import random
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from checklist.models import FotoChecklist, RespuestaChecklist
from clientes.models import Cliente, Ubicacion
from cotizaciones.models import DetalleCotizacion, ItemLogistica, ItemManoObra
from equipos.models import Equipo, TipoEquipo
from personal.models import PersonalEjecutor, Tecnico
from servicios.models import EstadoServicio, Servicio, TipoServicio

FOTO_DEMO_ORIGEN = Path(settings.BASE_DIR) / "reportes" / "static" / "reportes" / "damol_logo.jpg"

PERSONAL_DEMO = [
    # (nombres, apellidos, dni, cargo)
    ("Bruno", "Trujillo Taboada", "70000001", "Planner de mantenimiento"),
    ("Luis", "Párraga Valverde", "70000002", "Supervisor Operativo"),
    ("Christian", "Huaricapcha Alania", "70000003", "Supervisor SSOMA"),
    ("Jean Paul", "Ojeda Gregorio", "70000004", "Técnico Electricista"),
    ("Gerardo", "Pulache Mauricio", "70000005", "Técnico Mecánico"),
    ("Elvis", "León Chávez", "70000006", "Ayudante Mecánico"),
]


class Command(BaseCommand):
    help = (
        "Carga datos de demo reales (Volcan / Andaychagua, personal, y una cotización preventivo "
        "ya avanzada) para no depender de 'Cliente de Prueba' en una presentación. Repetible: "
        "usa get_or_create donde tiene sentido, y borra+recrea la cotización de demo cada vez."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        cliente, _ = Cliente.objects.update_or_create(
            codigo_corto="VOLCAN",
            defaults={
                "razon_social": "Volcan Compañía Minera S.A.A.",
                "ruc": "20100099999",  # RUC de prueba, formato válido — no es el RUC real de Volcan
                "direccion": "Unidad Andaychagua, Yauli, Junín",
                "contacto_nombre": "Bruno Trujillo Taboada",
                "contacto_telefono": "999888777",
                "contacto_email": "planner.andaychagua@volcan-demo.pe",
            },
        )
        ubicacion_unidad, _ = Ubicacion.objects.get_or_create(cliente=cliente, nombre="Unidad Andaychagua")
        ubicacion_pool, _ = Ubicacion.objects.get_or_create(
            cliente=cliente, nombre="Pool Cureña", defaults={"direccion": "Unidad Andaychagua"}
        )

        tipo_equipo, _ = TipoEquipo.objects.get_or_create(nombre="Grúa pórtico")
        equipo, _ = Equipo.objects.update_or_create(
            cliente=cliente,
            codigo_interno="PG-ANDAYCHAGUA-01",
            defaults={
                "tipo_equipo": tipo_equipo,
                "ubicacion": ubicacion_pool,
                "marca_estructura": "Estructura genérica",
                "marca_polipasto": "Konecranes",
                "capacidad_ton": 28,
                "especificaciones": {
                    "span": "11.7 m",
                    "altura_elevacion": "10.6 m",
                    "voltaje_potencia": "440V",
                    "voltaje_control": "110V",
                },
            },
        )

        tecnicos = {}
        for nombres, apellidos, dni, cargo in PERSONAL_DEMO:
            tecnico, _ = Tecnico.objects.update_or_create(
                dni=dni, defaults={"nombres": nombres, "apellidos": apellidos, "cargo_habitual": cargo}
            )
            tecnicos[dni] = tecnico
        self.stdout.write(self.style.SUCCESS(f"Personal: {len(tecnicos)} técnico(s) listos."))

        # La cotización de demo se recrea desde cero cada vez que se corre el comando, para que
        # sea segura de repetir sin ir acumulando duplicados si algo se ensucia antes de la reunión.
        Servicio.objects.filter(cliente=cliente, titulo="DEMO — Mantenimiento preventivo").delete()

        servicio = Servicio.objects.create(
            cliente=cliente,
            equipo=equipo,
            ubicacion=ubicacion_pool,
            tipo_servicio=TipoServicio.PREVENTIVO,
            titulo="DEMO — Mantenimiento preventivo",
            elaborado_por="Bruno Trujillo Taboada",
            moneda="PEN",
        )
        servicio.estado = EstadoServicio.EN_EJECUCION
        servicio.save()

        PersonalEjecutor.objects.create(servicio=servicio, tecnico=tecnicos["70000005"], rol="Técnico Mecánico")
        PersonalEjecutor.objects.create(servicio=servicio, tecnico=tecnicos["70000004"], rol="Técnico Electricista")
        PersonalEjecutor.objects.create(servicio=servicio, tecnico=tecnicos["70000006"], rol="Ayudante Mecánico")

        detalle = DetalleCotizacion.objects.create(
            servicio=servicio,
            porcentaje_indirectos=10,
            porcentaje_utilidad_servicio=20,
            porcentaje_utilidad_repuestos=15,
        )
        ItemManoObra.objects.create(detalle=detalle, descripcion="Técnico mecánico (día)", cantidad=2, costo_unitario=180, orden=0)
        ItemManoObra.objects.create(detalle=detalle, descripcion="Técnico electricista (día)", cantidad=1, costo_unitario=190, orden=1)
        ItemLogistica.objects.create(detalle=detalle, descripcion="Movilidad local", cantidad=1, costo_unitario=80, orden=0)
        detalle.recalcular()

        # Checklist: se generó automático al crear el Servicio (preventivo). Marcamos 3 sistemas
        # con una mezcla B/R realista — no todo perfecto, para que se vea como una visita real.
        sistemas_a_marcar = [1, 2, 4]  # Polipasto, Trolley/Carro, Componentes eléctricos del polipasto
        respuestas = list(
            RespuestaChecklist.objects.filter(
                servicio=servicio, item__sistema__orden__in=sistemas_a_marcar
            ).select_related("item")
        )
        random.seed(42)  # resultado repetible entre corridas
        primera_foto_puesta = False
        for respuesta in respuestas:
            respuesta.estado = "R" if random.random() < 0.2 else "B"
            if respuesta.estado == "R":
                respuesta.observacion = "Desgaste leve, seguimiento en próxima visita."
            respuesta.save()
            if not primera_foto_puesta and FOTO_DEMO_ORIGEN.exists():
                destino_rel = f"checklist_fotos/demo/{respuesta.pk}_demo.jpg"
                destino_abs = Path(settings.MEDIA_ROOT) / destino_rel
                destino_abs.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(FOTO_DEMO_ORIGEN, destino_abs)
                FotoChecklist.objects.create(
                    respuesta=respuesta, imagen=destino_rel, descripcion="Estado general — vista de referencia"
                )
                primera_foto_puesta = True

        self.stdout.write(self.style.SUCCESS(f"Cotización de demo: {servicio.codigo} (id={servicio.pk})"))
        self.stdout.write(
            self.style.SUCCESS(
                f"  {len(respuestas)} ítems de checklist marcados en 3 sistemas, "
                f"{'con' if primera_foto_puesta else 'sin'} foto de ejemplo."
            )
        )
        self.stdout.write(self.style.SUCCESS(f"  Total: {servicio.monto_total} {servicio.moneda}"))
        self.stdout.write(self.style.WARNING("Segunda cotización (cliente nuevo, flujo en vivo): NO se precarga a propósito."))
