# gestionCitas/urls.py
from django.urls import path
from . import views

app_name = 'gestionCitas'

urlpatterns = [
    path('calendario/', views.calendario_mes, name='calendario_mes'),
    path('dia/', views.agenda_dia, name='agenda_dia'),
    path('agendar/<str:bloque_id>/', views.agendar_cita, name='agendar_cita'),
    path('cancelar-bloques/<str:bloque_id>/', views.cancelar_bloques_veterinario, name='cancelar_bloques_veterinario'),
    path('reprogramar/<str:bloque_id>/', views.reprogramar_cita, name='reprogramar_cita'),
    path('reprogramar/', views.reprogramar_cita_page, name='reprogramar_cita_page'),
    path('agregar-disponibilidad/<str:fecha>/<str:veterinario_id>/', views.agregar_disponibilidad, name='agregar_disponibilidad'),
    
    # AJAX endpoints
    path('api/buscar-cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('api/buscar-mascotas/', views.buscar_mascotas_cliente, name='buscar_mascotas_cliente'),
    path('api/buscar-mascota/', views.buscar_mascota, name='buscar_mascota'),
]
