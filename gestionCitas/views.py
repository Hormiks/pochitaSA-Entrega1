from django.shortcuts import render, get_object_or_404, redirect
from datetime import date, datetime
from calendar import monthrange
import uuid
from main.decorators import roles_requeridos
from django.contrib import messages
from django.http import JsonResponse
from .models import BloqueAtencion, Veterinario, Cliente, Mascota   
from .forms import CancelarBloquesForm, ReprogramarCitaForm, ClienteForm, MascotaForm  
from django.contrib.auth.decorators import login_required


def actualizar_citas_completadas():
    """
    Actualiza automáticamente las citas RESERVADAS cuya fecha ya pasó a COMPLETADA.
    """
    hoy = date.today()
    BloqueAtencion.objects.filter(
        estado='RESERVADO',
        fecha__lt=hoy
    ).update(estado='COMPLETADA')


# Create your views here.
# ===== HU002: Calendario mensual y agendar hora =====

@roles_requeridos("Recepcionista")
def calendario_mes(request):
    """Muestra el mes en curso con los bloques por veterinario."""
    # Actualizar citas pasadas a COMPLETADA
    actualizar_citas_completadas()
    
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
        'veterinario_seleccionado': veterinario_id if veterinario_id else None,
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


def _normalizar_rut(rut: str) -> str:
    return (rut or '').replace('.', '').replace('-', '').replace(' ', '').upper().strip()

@roles_requeridos("Recepcionista")
def agendar_cita(request, bloque_id):
    bloque = get_object_or_404(BloqueAtencion, pk=bloque_id)

    if bloque.estado not in ['DISPONIBLE', 'CANCELADO_VET']:
        messages.error(request, 'Este bloque no está disponible para agendar.')
        return redirect('gestionCitas:calendario_mes')

    if bloque.mascota is not None and bloque.estado == 'RESERVADO':
        messages.error(request, 'Este bloque ya tiene una cita agendada.')
        return redirect('gestionCitas:calendario_mes')

    if request.method == 'POST':
        post = request.POST.copy()

        rut = _normalizar_rut(post.get('cliente-rut_cli', ''))
        post['cliente-rut_cli'] = rut

        chip = (post.get('mascota-codigo_chip', '') or '').strip()
        post['mascota-codigo_chip'] = chip

        cliente_instance = Cliente.objects.filter(rut_cli=rut).first()
        mascota_instance = Mascota.objects.select_related('dueño').filter(codigo_chip=chip).first()

        cliente_form = ClienteForm(post, prefix='cliente', instance=cliente_instance)
        mascota_form = MascotaForm(post, prefix='mascota', instance=mascota_instance)

        if cliente_form.is_valid() and mascota_form.is_valid():
            cliente = cliente_form.save()  # crea o actualiza (si venía instance)

            # Si el chip existe pero pertenece a otro dueño, lo bloqueamos (recomendado)
            if mascota_instance and mascota_instance.dueño_id != cliente.rut_cli:
                mascota_form.add_error('codigo_chip', 'Este código de chip ya está asociado a otro cliente.')
            else:
                mascota = mascota_form.save(commit=False)
                mascota.dueño = cliente
                mascota.save()

                bloque.mascota = mascota
                bloque.motivo_consulta = (post.get('motivo_consulta') or '').strip()[:30]
                bloque.codigo_cita = uuid.uuid4().hex[:10].upper()
                bloque.estado = 'RESERVADO'
                bloque.save()

                messages.success(request, 'Cita agendada correctamente.')
                return redirect('gestionCitas:calendario_mes')

        messages.error(request, 'Revise los errores del formulario.')
    else:
        cliente_form = ClienteForm(prefix='cliente')
        mascota_form = MascotaForm(prefix='mascota')

    return render(request, 'gestionCitas/agendar_cita.html', {
        'bloque': bloque,
        'cliente_form': cliente_form,
        'mascota_form': mascota_form,
    })

@roles_requeridos("Recepcionista")
def agenda_dia(request):
    """
    Muestra la agenda de un día específico separada en:
    - Horarios ocupados (bloques con mascota asignada)
    - Horarios libres (bloques sin mascota, disponibles o cancelados)
    """
    # Actualizar citas pasadas a COMPLETADA
    actualizar_citas_completadas()

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
        vet_seleccionado = veterinario_id

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
    bloque = get_object_or_404(BloqueAtencion, pk=bloque_id)
    
    if request.method == 'POST':
        bloque.estado = 'CANCELADO_VET'
        bloque.save()
        
        messages.success(request, f"Bloque #{bloque_id} cancelado correctamente.")
        # Redirigir a la página de origen si se especifica
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('gestionCitas:calendario_mes')
    
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
        return redirect('gestionCitas:calendario_mes')
    if request.method == 'POST':
        form = ReprogramarCitaForm(request.POST, veterinario=bloque_original.veterinario)
        if form.is_valid():
            nuevo_bloque = form.cleaned_data['nuevo_bloque']   # Pasar datos de la cita al nuevo bloque
            nuevo_bloque.mascota = bloque_original.mascota
            nuevo_bloque.motivo_consulta = bloque_original.motivo_consulta
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


@roles_requeridos("Recepcionista")
def agregar_disponibilidad(request, fecha, veterinario_id='0'):
    """
    Abre un formulario para agregar bloques de disponibilidad en una fecha específica.
    """
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, 'Formato de fecha inválido.')
        return redirect('gestionCitas:calendario_mes')
    
    veterinario = None
    if veterinario_id != '0':
        try:
            veterinario = Veterinario.objects.get(rut_vet=veterinario_id)
        except Veterinario.DoesNotExist:
            messages.error(request, 'Veterinario no encontrado.')
            return redirect('gestionCitas:calendario_mes')
    
    if request.method == 'POST':
        vet_id = request.POST.get('veterinario')
        hora_inicio_str = request.POST.get('hora_inicio')
        hora_fin_str = request.POST.get('hora_fin')
        
        if not vet_id or not hora_inicio_str or not hora_fin_str:
            messages.error(request, 'Debes completar todos los campos.')
            return redirect('gestionCitas:agregar_disponibilidad', fecha=fecha, veterinario_id=veterinario_id)
        
        try:
            veterinario = Veterinario.objects.get(rut_vet=vet_id)
        except Veterinario.DoesNotExist:
            messages.error(request, 'Veterinario no encontrado.')
            return redirect('gestionCitas:agregar_disponibilidad', fecha=fecha, veterinario_id=veterinario_id)
        
        try:
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Formato de hora inválido. Usa HH:MM.')
            return redirect('gestionCitas:agregar_disponibilidad', fecha=fecha, veterinario_id=veterinario_id)
        
        # Verificar que la hora de inicio sea anterior a la de fin
        if hora_inicio >= hora_fin:
            messages.error(request, 'La hora de inicio debe ser anterior a la de fin.')
            return redirect('gestionCitas:agregar_disponibilidad', fecha=fecha, veterinario_id=veterinario_id)
        
        # Generar codigo_atencion único (máx 10 caracteres)
        codigo_atencion = uuid.uuid4().hex[:10].upper()
        
        # Crear el bloque
        bloque = BloqueAtencion.objects.create(
            codigo_atencion=codigo_atencion,
            veterinario=veterinario,
            fecha=fecha_obj,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado='DISPONIBLE'
        )
        
        messages.success(request, 'Bloque de disponibilidad agregado correctamente.')
        return redirect('gestionCitas:calendario_mes')
    
    veterinarios = Veterinario.objects.all()
    context = {
        'fecha': fecha_obj,
        'veterinario': veterinario,
        'veterinarios': veterinarios,
    }
    return render(request, 'gestionCitas/agregar_disponibilidad.html', context)


# ===== AJAX Endpoints =====

@roles_requeridos("Recepcionista")
@login_required
def buscar_cliente(request):
    rut = request.GET.get('rut', '').strip()
    if not rut:
        return JsonResponse({'encontrado': False})
    
    try:
        cliente = Cliente.objects.get(rut_cli=rut)
        return JsonResponse({
            'encontrado': True,
            'nombre': cliente.nombre,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'direccion': cliente.direccion,
        })
    except Cliente.DoesNotExist:
        return JsonResponse({'encontrado': False})

@login_required
@roles_requeridos("Recepcionista")
def buscar_mascotas_cliente(request):
    rut = request.GET.get('rut', '').strip()
    if not rut:
        return JsonResponse({'mascotas': []})
    
    try:
        cliente = Cliente.objects.get(rut_cli=rut)
        mascotas = cliente.mascotas.all()
        data = [{
            'codigo_chip': m.codigo_chip,
            'nombre': m.nombre,
            'especie': m.especie,
            'raza': m.raza,
            'edad': m.edad,
            'peso': str(m.peso) if m.peso else '',
        } for m in mascotas]
        return JsonResponse({'mascotas': data})
    except Cliente.DoesNotExist:
        return JsonResponse({'mascotas': []})


@login_required
def buscar_mascota(request):
    """Busca una mascota por código de chip y retorna sus datos."""
    codigo = request.GET.get('codigo', '').strip()
    if not codigo:
        return JsonResponse({'encontrada': False})
    
    try:
        mascota = Mascota.objects.get(codigo_chip=codigo)
        return JsonResponse({
            'encontrada': True,
            'codigo_chip': mascota.codigo_chip,
            'nombre': mascota.nombre,
            'especie': mascota.especie,
            'raza': mascota.raza,
            'edad': mascota.edad,
            'peso': str(mascota.peso) if mascota.peso else '',
            'dueno_rut': mascota.dueño.rut_cli,
            'dueno_nombre': mascota.dueño.nombre,
            'dueno_telefono': mascota.dueño.telefono,
            'dueno_email': mascota.dueño.email,
            'dueno_direccion': mascota.dueño.direccion,
        })
    except Mascota.DoesNotExist:
        return JsonResponse({'encontrada': False})

def buscar_mascota(request):
    chip = (request.GET.get('chip', '') or '').strip()
    if not chip:
        return JsonResponse({'encontrado': False})

    try:
        m = Mascota.objects.select_related('dueño').get(codigo_chip=chip)
        return JsonResponse({
            'encontrado': True,
            'nombre': m.nombre,
            'especie': m.especie,
            'raza': m.raza,
            'edad': m.edad if m.edad is not None else '',
            'peso': str(m.peso) if m.peso is not None else '',
            'rut_dueno': m.dueño.rut_cli,
        })
    except Mascota.DoesNotExist:
        return JsonResponse({'encontrado': False})