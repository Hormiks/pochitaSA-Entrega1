from django.contrib import admin
from .models import Cliente, Mascota, Veterinario, BloqueAtencion

# Register your models here.
admin.site.register(Cliente)
admin.site.register(Mascota)
admin.site.register(Veterinario)
admin.site.register(BloqueAtencion)
