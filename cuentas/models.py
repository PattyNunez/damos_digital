from django.conf import settings
from django.db import models


class Rol(models.TextChoices):
    TECNICO = "tecnico", "Técnico"
    COMERCIAL = "comercial", "Comercial"
    ADMINISTRADOR = "administrador", "Administrador"


class Perfil(models.Model):
    """Rol de acceso de un usuario. Modelo simple a propósito (no Groups/Permissions
    nativos de Django): son 3 roles fijos que gatean áreas completas de la app, no
    permisos finos por modelo — no hace falta la maquinaria de permisos de Django."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="perfil", on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=Rol.choices)
    tecnico = models.ForeignKey(
        "personal.Tecnico",
        related_name="perfiles",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Solo si el rol es Técnico: qué registro de personal corresponde a este usuario, para filtrar 'Mis servicios'.",
    )

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.usuario} ({self.get_rol_display()})"
