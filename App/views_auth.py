# views_auth.py
"""
Vistas de autenticación personalizada para LogiCo
Login, Logout y Registro de usuarios
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroForm
from .roles import obtener_rol_usuario


def login_view(request):
    """Vista de inicio de sesión personalizado"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            rol = obtener_rol_usuario(usuario)
            messages.success(request, f'¡Bienvenido {usuario.username}! (Rol: {rol})')
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})


def registro_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, 
                f'¡Usuario "{usuario.username}" registrado exitosamente! '
                'Por favor, inicia sesión.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'registro.html', {'form': form})


@login_required(login_url='login')
def logout_view(request):
    """Vista para cerrar sesión"""
    nombre_usuario = request.user.username
    logout(request)
    messages.success(request, f'¡Hasta pronto {nombre_usuario}!')
    return redirect('login')


def acceso_denegado(request):
    """Página de acceso denegado"""
    return render(request, 'acceso_denegado.html', status=403)