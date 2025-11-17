# views_configuracion.py
"""
Vistas para la configuración del usuario y del sistema
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .roles import obtener_rol_usuario, obtener_permisos_usuario, MODULOS, ROLES
from .auth_decorators import solo_admin


@login_required(login_url='login')
def configuracion(request):
    """Panel principal de configuración"""
    rol_usuario = obtener_rol_usuario(request.user)
    permisos = obtener_permisos_usuario(request.user)
    
    # Contar módulos accesibles
    modulos_accesibles = {}
    for modulo, nombre in MODULOS.items():
        if modulo in permisos and permisos[modulo]:
            modulos_accesibles[modulo] = nombre
    
    context = {
        'rol_usuario': rol_usuario,
        'permisos': permisos,
        'modulos_accesibles': modulos_accesibles,
        'total_modulos': len(modulos_accesibles),
    }
    
    return render(request, 'panel_configuracion.html', context)


@login_required(login_url='login')
def mis_permisos(request):
    """Ver los permisos del usuario actual"""
    rol_usuario = obtener_rol_usuario(request.user)
    permisos = obtener_permisos_usuario(request.user)
    
    # Formatear permisos para mostrar
    permisos_formateados = {}
    for modulo, acciones in permisos.items():
        if acciones:
            permisos_formateados[MODULOS.get(modulo, modulo)] = acciones
    
    context = {
        'rol_usuario': rol_usuario,
        'permisos': permisos_formateados,
    }
    
    return render(request, 'mis_permisos.html', context)


@solo_admin
def gestionar_usuarios(request):
    """Gestionar usuarios y roles (solo admin)"""
    usuarios = User.objects.all().order_by('-date_joined')
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'gestionar_usuarios.html', context)


@solo_admin
def asignar_rol(request, user_id):
    """Asignar rol a un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        rol = request.POST.get('rol')
        
        # Remover grupos anteriores
        usuario.groups.clear()
        
        # Asignar nuevo grupo
        if rol and rol != 'admin':
            grupo, created = Group.objects.get_or_create(name=rol)
            usuario.groups.add(grupo)
            usuario.is_staff = False
            usuario.is_superuser = False
        elif rol == 'admin':
            usuario.is_staff = True
            usuario.is_superuser = True
        else:
            usuario.is_staff = False
            usuario.is_superuser = False
        
        usuario.save()
        messages.success(request, f'Rol asignado a {usuario.username} exitosamente.')
        return redirect('gestionar_usuarios')
    
    # Obtener rol actual
    rol_actual = obtener_rol_usuario(usuario)
    
    context = {
        'usuario': usuario,
        'rol_actual': rol_actual,
        'roles': ROLES,
    }
    
    return render(request, 'asignar_rol.html', context)


@login_required(login_url='login')
def cambiar_contrasena(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Personalizar widgets del formulario
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    
    context = {
        'form': form,
    }
    
    return render(request, 'cambiar_contrasena.html', context)


@login_required(login_url='login')
def preferencias(request):
    """Gestionar preferencias del usuario usando sesión"""
    
    # Si no existen preferencias en la sesión, inicializamos valores por defecto
    if 'preferencias' not in request.session:
        request.session['preferencias'] = {
            'tema': 'claro',
            'notif_email': True,
            'notif_sms': False,
            'idioma': 'es',
        }

    preferencias = request.session['preferencias']

    if request.method == 'POST':
        preferencias['tema'] = request.POST.get('tema', 'claro')
        preferencias['notif_email'] = 'notif_email' in request.POST
        preferencias['notif_sms'] = 'notif_sms' in request.POST
        preferencias['idioma'] = request.POST.get('idioma', 'es')

        request.session['preferencias'] = preferencias  # Guardar cambios en la sesión
        messages.success(request, 'Preferencias guardadas exitosamente.')
        return redirect('preferencias')

    context = {
        'preferencias': preferencias,
    }

    return render(request, 'preferencias.html', context)
