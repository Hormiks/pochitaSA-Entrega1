from django.shortcuts import render
from datetime import date, datetime
from calendar import monthrange
from main.decorators import roles_requeridos
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import BloqueAtencion, Veterinario
from .forms import AgendarCitaForm, CancelarBloquesForm, ReprogramarCitaForm
from django.contrib.auth.decorators import login_required

# Create your views here.
# ===== HU002: Calendario mensual y agendar hora =====

@roles_requeridos("Recepcionista")
def calendario_mes(request):
    """Muestra el mes en curso con los bloques por veterinario."""
    hoy = date.today()
    
    # Obtener el año y mes de la URL
    year = int(request.GET.get('year', hoy.year))
    month = int(request.GET.get('month', hoy.month))

    # Filtro opcional por veterinario
    veterinario_id = request.GET.get('veterinario')
    if veterinario_id:
        bloques_base = BloqueAtencion.objects.filter(veterinario_id=veterinario_id)
    else:
        bloques_base = BloqueAtencion.objects.all()

    # Obtener el primer día de la semana y número de días del mes
    primer_dia_semana, num_dias = monthrange(year, month)

    dias = []
    for dia in range(1, num_dias + 1):
        fecha_dia = date(year, month, dia)
        bloques_dia = bloques_base.filter(fecha=fecha_dia).select_related('veterinario', 'mascota')
        dias.append({'fecha': fecha_dia, 'bloques': bloques_dia})

    # Armar semanas (para dibujar un calendario tipo tabla)
    semanas = []
    semana = []

    # Espacios en blanco antes del primer día
    for _ in range(primer_dia_semana):
        semana.append(None)

    for info_dia in dias:
        semana.append(info_dia)
        if len(semana) == 7:
            semanas.append(semana)
            semana = []

    if semana:
        while len(semana) < 7:
            semana.append(None)
        semanas.append(semana)

    # Crear una lista de meses
    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    # Lista de años (por ejemplo, el año actual y el anterior/futuro)
    anios = [year - 1, year, year + 1]

    veterinarios = Veterinario.objects.all()
    # Nombre legible del mes seleccionado
    month_name = next((nombre for num, nombre in meses if num == month), '')

    # Nombre del veterinario seleccionado (si aplica)
    veterinario_nombre = None
    if veterinario_id:
        try:
            veterinario_nombre = Veterinario.objects.get(pk=veterinario_id).nombre
        except Veterinario.DoesNotExist:
            veterinario_nombre = None

    context = {
        'semanas': semanas,
        'year': year,
        'month': month,
        'veterinarios': veterinarios,
        'veterinario_seleccionado': int(veterinario_id) if veterinario_id else None,
        'meses': meses,
        'mes_seleccionado': month,
        'anios': anios,
        'anio_seleccionado': year,
        # fecha para mostrar en plantilla (primer día del mes seleccionado)
        'fecha': date(year, month, 1),
        'month_name': month_name,
        'veterinario_nombre': veterinario_nombre,
    }
    return render(request, 'gestionCitas/calendario_mes.html', context)

@roles_requeridos("Recepcionista")
def agendar_cita(request, bloque_id):
    """La recepcionista agenda una cita sobre un bloque DISPONIBLE."""
    bloque = get_object_or_404(BloqueAtencion, pk=bloque_id, estado='DISPONIBLE')

    if request.method == 'POST':
        form = AgendarCitaForm(request.POST, instance=bloque)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.estado = 'RESERVADO'
            cita.save()
            messages.success(request, 'Cita agendada correctamente.')
            return redirect('gestionCitas:calendario_mes')
    else:
        form = AgendarCitaForm(instance=bloque)

    return render(request, 'gestionCitas/agendar_cita.html', {
        'bloque': bloque,
        'form': form,
    })

@roles_requeridos("Recepcionista")
def agenda_dia(request):
    """
    Muestra la agenda de un día específico separada en:
    - Horarios ocupados (bloques con mascota asignada)
    - Horarios libres (bloques sin mascota, disponibles o cancelados)
    """

    # Fecha seleccionada (GET ?fecha=YYYY-MM-DD), por defecto hoy
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    # Filtro opcional por veterinario
    veterinario_id = request.GET.get('veterinario')
    vet_seleccionado = None
    bloques_qs = BloqueAtencion.objects.filter(fecha=fecha).select_related(
        'veterinario', 'mascota', 'mascota__dueño'
    )

    if veterinario_id:
        bloques_qs = bloques_qs.filter(veterinario_id=veterinario_id)
        vet_seleccionado = int(veterinario_id)

    bloques_qs = bloques_qs.order_by('hora_inicio')

    # Separar en ocupados y libres
    bloques_ocupados = [b for b in bloques_qs if b.mascota is not None and b.estado != 'CANCELADO_VET']
    bloques_libres = [b for b in bloques_qs if b.mascota is None or b.estado == 'CANCELADO_VET']

    veterinarios = Veterinario.objects.all()

    context = {
        'fecha': fecha,
        'bloques_ocupados': bloques_ocupados,
        'bloques_libres': bloques_libres,
        'veterinarios': veterinarios,
        'veterinario_seleccionado': vet_seleccionado,
    }
    return render(request, 'gestionCitas/agenda_dia.html', context)

# ===== HU006: Replanificar cuando el veterinario cancela =====

@roles_requeridos("Recepcionista")
def cancelar_bloques_veterinario(request, bloque_id):
    """
    Cancela un bloque específico de atención.
    """
    bloque = get_object_or_404(BloqueAtencion, id=bloque_id)
    
    if request.method == 'POST':
        bloque.estado = 'CANCELADO_VET'
        bloque.save()
        
        messages.success(request, f"Bloque #{bloque_id} cancelado correctamente.")
        return redirect('gestionCitas:agenda_dia')
    
    # GET: mostrar confirmación
    context = {
        'bloque': bloque,
    }
    return render(request, 'gestionCitas/cancelar_bloques_veterinario.html', context)


@roles_requeridos("Recepcionista")
def reprogramar_cita(request, bloque_id):
    """
    Reprograma una cita de un bloque (normalmente cancelado) a otro bloque disponible.
    """
    bloque_original = get_object_or_404(BloqueAtencion, pk=bloque_id)

    if bloque_original.mascota is None:
        messages.error(request, 'Este bloque no tiene paciente asignado.')
        return redirect('gestionCitas:cancelar_bloques_veterinario')

    if request.method == 'POST':
        form = ReprogramarCitaForm(request.POST, veterinario=bloque_original.veterinario)
        if form.is_valid():
            nuevo_bloque = form.cleaned_data['nuevo_bloque']

            # Pasar datos de la cita al nuevo bloque
            nuevo_bloque.mascota = bloque_original.mascota
            nuevo_bloque.motivo = bloque_original.motivo
            nuevo_bloque.estado = 'RESERVADO'
            nuevo_bloque.save()

            # Aseguramos que el original quede como cancelado por el vet
            bloque_original.estado = 'CANCELADO_VET'
            bloque_original.save()

            messages.success(request, 'Cita reprogramada correctamente.')
            return redirect('gestionCitas:calendario_mes')
    else:
        form = ReprogramarCitaForm(veterinario=bloque_original.veterinario)

    return render(request, 'gestionCitas/reprogramar_cita.html', {
        'bloque_original': bloque_original,
        'form': form,
    })





@roles_requeridos("Recepcionista")
def reprogramar_cita_page(request):
    """Renderiza la plantilla de reprogramación sin un bloque original específico.
    Útil para la versión general a la que el botón superior debe redirigir.
    """
    form = ReprogramarCitaForm()
    # plantilla espera 'bloque_original' con atributos; pasar un dict seguro
    bloque_original = {'fecha': '', 'hora_inicio': '', 'hora_fin': ''}

    return render(request, 'gestionCitas/reprogramar_cita.html', {
        'bloque_original': bloque_original,
        'form': form,
    })
