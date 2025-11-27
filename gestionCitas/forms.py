# gestionCitas/forms.py
from django import forms
from .models import BloqueAtencion, Mascota, Veterinario

class AgendarCitaForm(forms.ModelForm):
    class Meta:
        model = BloqueAtencion
        fields = ['mascota', 'motivo']
        labels = {
            'mascota': 'Mascota',
            'motivo': 'Motivo de la consulta',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Podrías filtrar por cliente si después agregas login, etc.
        self.fields['mascota'].queryset = Mascota.objects.all()


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
