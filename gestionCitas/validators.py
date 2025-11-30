import re
from django.core.exceptions import ValidationError

def validar_rut(value):
    # Eliminar cualquier guion, espacio si está presente
    value = value.replace('-', '').replace(' ', '').replace('.', '').upper().strip()

    patron = re.compile(r"^(\d{7,8})([0-9K])$")

    if not patron.match(value):
        raise ValidationError("El formato del RUT no es válido. Ingresa sin guiones (ej: 123456789 o 12345678K)")


def validar_numeros(value):
    if not value.isdigit():  # Verifica si el valor contiene solo dígitos
        raise ValidationError("El valor debe contener solo números.")
