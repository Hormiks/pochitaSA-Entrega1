# main/management/commands/crear_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Crea los roles (grupos) base del sistema."

    def handle(self, *args, **options):
        recep, created = Group.objects.get_or_create(name="Recepcionista")

        # Permisos básicos (principalmente útiles en admin, pero ordenan el modelo mental)
        permisos_codenames = [
            # BloqueAtencion
            "view_bloqueatencion", "add_bloqueatencion", "change_bloqueatencion",
            # Mascota / Cliente / Veterinario (solo lectura por ahora)
            "view_mascota", "view_cliente", "view_veterinario",
        ]

        perms = Permission.objects.filter(codename__in=permisos_codenames)
        recep.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS("Roles creados/actualizados: Recepcionista"))
