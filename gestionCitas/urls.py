# gestionCitas/urls.py
from django.urls import path
from . import views

app_name = 'gestionCitas'

urlpatterns = [
    path('calendario/', views.calendario_mes, name='calendario_mes'),
    path('dia/', views.agenda_dia, name='agenda_dia'),
    path('agendar/<int:bloque_id>/', views.agendar_cita, name='agendar_cita'),
    path('cancelar-bloques/<int:bloque_id>/', views.cancelar_bloques_veterinario, name='cancelar_bloques_veterinario'),
    path('reprogramar/<int:bloque_id>/', views.reprogramar_cita, name='reprogramar_cita'),
    # Página general para acceder a la interfaz de reprogramación (sin bloque específico)
    path('reprogramar/', views.reprogramar_cita_page, name='reprogramar_cita_page'),
]
