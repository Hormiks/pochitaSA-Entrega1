# gestionCitas/forms.py
from django import forms
from .models import BloqueAtencion, Mascota, Veterinario, Cliente


class CancelarBloquesForm(forms.Form):
    veterinario = forms.ModelChoiceField(queryset=Veterinario.objects.all())
    fecha_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


class ReprogramarCitaForm(forms.Form):
    nuevo_bloque = forms.ModelChoiceField(
        queryset=BloqueAtencion.objects.none(),
        label='Nuevo bloque disponible'
    )

    def __init__(self, *args, **kwargs):
        veterinario = kwargs.pop('veterinario', None)
        super().__init__(*args, **kwargs)

        qs = BloqueAtencion.objects.filter(estado='DISPONIBLE')
        if veterinario:
            qs = qs.filter(veterinario=veterinario)
        self.fields['nuevo_bloque'].queryset = qs.order_by('fecha', 'hora_inicio')


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut_cli', 'nombre', 'telefono', 'email', 'direccion']

    def clean_rut_cli(self):
        rut = (self.cleaned_data.get('rut_cli') or '')
        return rut.replace('-', '').replace(' ', '').replace('.', '').upper().strip()


class MascotaForm(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = ['codigo_chip', 'nombre', 'especie', 'raza', 'edad', 'peso']

    def clean_codigo_chip(self):
        return (self.cleaned_data.get('codigo_chip') or '').strip()
