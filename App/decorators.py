from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required as django_login_required
from django.http import HttpResponseForbidden
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy


# ============================================
# DECORADORES PARA FUNCIONES
# ============================================

def login_required(view_func):
    """
    Decorador personalizado que redirige a login si no está autenticado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_passes_test(test_func, login_url='login'):
    """
    Decorador personalizado para verificar condiciones de usuario.
    test_func debe retornar True/False.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login_url)
            if not test_func(request.user):
                return HttpResponseForbidden("No tienes permiso para acceder a esta vista.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rol_required(rol_list):
    """
    Decorador para verificar que el usuario tiene uno de los roles especificados.
    rol_list: lista de roles permitidos ej: ['ADMINISTRADOR', 'SUPERVISOR']
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.rol not in rol_list:
                return HttpResponseForbidden(f"Solo usuarios con roles {rol_list} pueden acceder.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rol_or_permissions(*roles_and_perms):
    """
    Decorador flexible que acepta roles O permisos.
    Ejemplo: @rol_or_permissions('ADMINISTRADOR', 'GERENTE', 'change_farmacia')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar si tiene alguno de los roles
            if hasattr(request.user, 'rol') and request.user.rol in roles_and_perms:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene alguno de los permisos
            for perm in roles_and_perms:
                if '.' not in perm:  # Si no tiene punto, es rol
                    continue
                if request.user.has_perm(perm):
                    return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("No tienes permiso para acceder a esta vista.")
        return wrapper
    return decorator


# ============================================
# MIXINS PARA VISTAS BASADAS EN CLASES
# ============================================

class LoginRequiredMixin:
    """
    Mixin para verificar que el usuario esté autenticado.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class UserPassesTestMixin:
    """
    Mixin para verificar condiciones de usuario.
    La subclase debe definir test_func(user) -> bool
    """
    test_func = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if self.test_func is None:
            raise NotImplementedError("test_func debe ser definido en la subclase")
        if not self.test_func(request.user):
            raise PermissionDenied("No tienes permiso para acceder a esta vista.")
        return super().dispatch(request, *args, **kwargs)


class RolRequiredMixin(LoginRequiredMixin):
    """
    Mixin para verificar que el usuario tenga uno de los roles especificados.
    
    Uso:
    class MiVista(RolRequiredMixin, View):
        roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']
    """
    roles_permitidos = []
    
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        
        if not hasattr(request.user, 'rol'):
            raise PermissionDenied("El usuario no tiene un rol asignado.")
        
        if request.user.rol not in self.roles_permitidos:
            raise PermissionDenied(
                f"Esta acción requiere uno de los siguientes roles: {', '.join(self.roles_permitidos)}"
            )
        
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class MultiRolRequiredMixin(LoginRequiredMixin):
    """
    Mixin flexible que acepta múltiples roles y/o permisos.
    
    Uso:
    class MiVista(MultiRolRequiredMixin, View):
        roles_o_permisos = ['ADMINISTRADOR', 'SUPERVISOR', 'change_farmacia']
    """
    roles_o_permisos = []
    
    def dispatch(self, request, *args, **kwargs):
        super().dispatch(request, *args, **kwargs)
        
        # Verificar roles
        if hasattr(request.user, 'rol') and request.user.rol in self.roles_o_permisos:
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        
        # Verificar permisos
        for perm in self.roles_o_permisos:
            if '.' in perm and request.user.has_perm(perm):
                return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        
        raise PermissionDenied(
            f"No tienes permiso. Requerido: {', '.join(self.roles_o_permisos)}"
        )


class SupervisorOAdminMixin(RolRequiredMixin):
    """
    Mixin especializado para Supervisor o Administrador.
    """
    roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']


class AdminOnlyMixin(RolRequiredMixin):
    """
    Mixin especializado para Administrador.
    """
    roles_permitidos = ['ADMINISTRADOR']


class OperadorOnlyMixin(RolRequiredMixin):
    """
    Mixin especializado para Operador.
    """
    roles_permitidos = ['OPERADOR']


class MotoristaOnlyMixin(RolRequiredMixin):
    """
    Mixin especializado para Motorista.
    """
    roles_permitidos = ['MOTORISTA']


class GerenteOnlyMixin(RolRequiredMixin):
    """
    Mixin especializado para Gerente.
    """
    roles_permitidos = ['GERENTE']


# ============================================
# FUNCIONES AUXILIARES PARA VERIFICACIÓN
# ============================================

def es_administrador(user):
    """Verifica si el usuario es administrador."""
    return hasattr(user, 'rol') and user.rol == 'ADMINISTRADOR'


def es_supervisor(user):
    """Verifica si el usuario es supervisor."""
    return hasattr(user, 'rol') and user.rol == 'SUPERVISOR'


def es_gerente(user):
    """Verifica si el usuario es gerente."""
    return hasattr(user, 'rol') and user.rol == 'GERENTE'


def es_operador(user):
    """Verifica si el usuario es operador."""
    return hasattr(user, 'rol') and user.rol == 'OPERADOR'


def es_motorista(user):
    """Verifica si el usuario es motorista."""
    return hasattr(user, 'rol') and user.rol == 'MOTORISTA'


def puede_editar_farmacia(user):
    """Verifica si el usuario puede editar farmacias."""
    return es_administrador(user) or es_supervisor(user)


def puede_editar_motorista(user):
    """Verifica si el usuario puede editar motoristas."""
    return es_administrador(user) or es_supervisor(user)


def puede_editar_moto(user):
    """Verifica si el usuario puede editar motos."""
    return es_administrador(user) or es_supervisor(user)


def puede_crear_asignacion_moto(user):
    """Verifica si el usuario puede crear asignaciones de moto."""
    return es_supervisor(user) or es_administrador(user)


def puede_crear_asignacion_farmacia(user):
    """Verifica si el usuario puede crear asignaciones de farmacia."""
    return es_supervisor(user) or es_administrador(user)


def puede_crear_despacho(user):
    """Verifica si el usuario puede crear despachos."""
    return es_operador(user) or es_supervisor(user) or es_administrador(user) or es_gerente(user)


def puede_cambiar_estado_despacho(user):
    """Verifica si el usuario puede cambiar el estado de despachos."""
    return es_motorista(user) or es_supervisor(user) or es_administrador(user) or es_gerente(user)
