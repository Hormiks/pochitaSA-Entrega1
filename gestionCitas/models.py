from django.db import models
from .validators import validar_rut, validar_numeros

class Cliente(models.Model):
    rut_cli = models.CharField(max_length=10, primary_key=True, validators=[validar_rut])  # RUT del cliente
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Mascota(models.Model):
    codigo_chip = models.CharField(max_length=15, primary_key=True, validators=[validar_numeros])  # Código del chip
    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raza = models.CharField(max_length=50, blank=True)
    edad = models.PositiveIntegerField(null=True, blank=True)  # Edad opcional
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Peso opcional
    dueño = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='mascotas')

    def __str__(self):
        return f"{self.nombre} ({self.especie})"


class Veterinario(models.Model):
    rut_vet = models.CharField(max_length=10, primary_key=True, validators=[validar_rut])  # RUT del veterinario
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class BloqueAtencion(models.Model):
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('RESERVADO', 'Reservado'),
        ('CANCELADO_VET', 'Cancelado por veterinario'),
        ('CANCELADO_PAC', 'Cancelado por paciente'),
    ]

    veterinario = models.ForeignKey(
        Veterinario,
        on_delete=models.CASCADE,
        related_name='bloques'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='DISPONIBLE'
    )

    mascota = models.ForeignKey(
        Mascota,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bloques'
    )
    motivo = models.TextField(blank=True)

    def __str__(self):
        return f"{self.fecha} {self.hora_inicio}-{self.hora_fin} / {self.veterinario}"
