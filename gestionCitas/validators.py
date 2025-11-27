import re
from django.core.exceptions import ValidationError

def validar_rut(value):
    # Eliminar cualquier guion si está presente
    value = value.replace('-', '').upper()

    patron = re.compile(r"^(\d{8})([0-9K])$")

    if not patron.match(value):
        raise ValidationError("El formato del RUT no es válido. El formato correcto es: 12345678-9")


def validar_numeros(value):
    if not value.isdigit():  # Verifica si el valor contiene solo dígitos
        raise ValidationError("El valor debe contener solo números.")
