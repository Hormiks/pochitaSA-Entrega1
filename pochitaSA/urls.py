"""
URL configuration for pochitaSA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from main import views
from django.contrib.auth import views as auth_views 
from django.conf import settings
from django.conf.urls.static import static
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    path('', views.index, name='index'),  # Redirige al index cuando se entra a la raíz
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('citas/', include('gestionCitas.urls')),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or BASE_DIR / 'static')