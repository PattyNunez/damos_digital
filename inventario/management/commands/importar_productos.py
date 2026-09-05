from django.core.management.base import BaseCommand, CommandError

from inventario.importador import importar_productos_desde_excel


class Command(BaseCommand):
    help = "Importa/actualiza productos desde un archivo Excel (.xlsx) con la plantilla de Damol Digital."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo .xlsx a importar.")

    def handle(self, *args, **options):
        ruta = options["archivo"]
        try:
            resultado = importar_productos_desde_excel(ruta)
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {ruta}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{resultado.creados} producto(s) creado(s), {resultado.actualizados} actualizado(s)."
            )
        )
        if resultado.proveedores_creados:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(resultado.proveedores_creados)} proveedor(es) nuevo(s) creado(s) "
                    "automáticamente (revisar posibles duplicados por tipeo):"
                )
            )
            for nombre in resultado.proveedores_creados:
                self.stdout.write(f"  - {nombre}")
        if resultado.errores:
            self.stdout.write(self.style.ERROR(f"{len(resultado.errores)} fila(s) con error:"))
            for error in resultado.errores:
                self.stdout.write(f"  - {error}")
