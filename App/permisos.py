from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class RolRequiredMixin(LoginRequiredMixin):
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'rol') and request.user.rol in self.roles_permitidos:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("No tienes permisos para acceder a esta vista.")
