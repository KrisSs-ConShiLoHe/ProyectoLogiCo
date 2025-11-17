# auth_decorators.py
"""
Decoradores para restricción de acceso según rol y permisos
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .roles import obtener_rol_usuario, tiene_permiso


def login_requerido(view_func):
    """
    Decorador para verificar que el usuario esté autenticado
    
    Uso:
        @login_requerido
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def rol_requerido(*roles_permitidos):
    """
    Decorador para verificar que el usuario tenga uno de los roles especificados
    
    Uso:
        @rol_requerido('admin', 'supervisor')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión.')
                return redirect('login')
            
            rol_usuario = obtener_rol_usuario(request.user)
            
            if rol_usuario not in roles_permitidos:
                messages.error(request, 'No tienes permiso para acceder a esta página.')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permiso_requerido(modulo, accion='view'):
    """
    Decorador para verificar que el usuario tenga un permiso específico
    
    Uso:
        @permiso_requerido('farmacias', 'view')
        def mi_vista(request):
            ...
        
        @permiso_requerido('farmacias', 'delete')
        def eliminar_farmacia(request, pk):
            ...
    
    Parámetros:
        modulo: Módulo a verificar (farmacias, motoristas, motos, asignaciones, etc)
        accion: Acción a verificar (view, add, change, delete)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión.')
                return redirect('login')
            
            if not tiene_permiso(request.user, modulo, accion):
                messages.error(request, 'No tienes permiso para realizar esta acción.')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def solo_admin(view_func):
    """
    Decorador para acceso solo de administradores
    
    Uso:
        @solo_admin
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión.')
            return redirect('login')
        
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, 'Solo administradores pueden acceder.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_motorista(view_func):
    """
    Decorador para acceso solo de motoristas
    
    Uso:
        @solo_motorista
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión.')
            return redirect('login')
        
        rol = obtener_rol_usuario(request.user)
        if rol != 'motorista':
            messages.error(request, 'Esta página es solo para motoristas.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_farmacia(view_func):
    """
    Decorador para acceso solo de farmacias
    
    Uso:
        @solo_farmacia
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión.')
            return redirect('login')
        
        rol = obtener_rol_usuario(request.user)
        if rol != 'farmacia':
            messages.error(request, 'Esta página es solo para farmacias.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def solo_supervisor(view_func):
    """
    Decorador para acceso solo de supervisores
    
    Uso:
        @solo_supervisor
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión.')
            return redirect('login')
        
        rol = obtener_rol_usuario(request.user)
        if rol != 'supervisor':
            messages.error(request, 'Esta página es solo para supervisores.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper