from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse


def index(request):
    # Si no hay sesión, manda a login.
    if not request.user.is_authenticated:
        return redirect("login")

    # Si el usuario está autenticado, muestra la página de inicio o un dashboard general
    return render(request, "main/index.html")  # El template que quieres mostrar


@login_required
def dashboard_redirect(request):
    u = request.user

    # Si el usuario es un recepcionista o superusuario, redirigir al index
    if u.is_superuser or u.groups.filter(name="Recepcionista").exists():
        return redirect('index')  # Redirigir al index, no al calendario

    # Si no es un recepcionista, redirige a otras páginas o un fallback
    return redirect('index')  # Esto redirige al index para otros roles también