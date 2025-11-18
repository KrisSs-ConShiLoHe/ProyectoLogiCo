"""
Vistas de Autenticación y Gestión de Contraseña
"""
from django.shortcuts import render, redirect
from django.views.generic import View, FormView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordChangeView, PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from django.views.generic import TemplateView
from django.utils.timezone import now
from ..decorators import LoginRequiredMixin
from ..forms import LoginForm, UserCreationForm


# ============================================
# VISTAS DE AUTENTICACIÓN
# ============================================

class LoginView(View):
    """
    Vista de inicio de sesión.
    """
    template_name = 'auth/login.html'
    form_class = LoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """
    Vista de cierre de sesión.
    """
    def get(self, request):
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('login')


class PasswordChangeView(LoginRequiredMixin, FormView):
    """
    Vista para cambiar contraseña del usuario autenticado.
    """
    template_name = 'auth/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Contraseña cambiada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al cambiar la contraseña.')
        return super().form_invalid(form)


class PasswordResetView(FormView):
    """
    Vista para solicitar restablecimiento de contraseña.
    """
    template_name = 'auth/password_reset.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(
            self.request,
            'Se ha enviado un correo con instrucciones para restablecer tu contraseña.'
        )
        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    """
    Vista para confirmar restablecimiento de contraseña.
    """
    template_name = 'auth/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        messages.success(self.request, 'Contraseña restablecida exitosamente.')
        return super().form_valid(form)


class SessionInfoView(LoginRequiredMixin, TemplateView):
    template_name = 'session_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.request.session
        now_ = now()

        login_ts = session.get('login_timestamp')
        ultima_ts = session.get('ultima_actividad')

        context.update({
            'session_key': session.session_key,
            'login_timestamp': datetime.fromisoformat(login_ts).strftime('%d/%m/%Y %H:%M:%S') if login_ts else None,
            'ultima_actividad': datetime.fromisoformat(ultima_ts).strftime('%d/%m/%Y %H:%M:%S') if ultima_ts else None,
            'tiempo_sesion': str(now_ - datetime.fromisoformat(login_ts)) if login_ts else None,
            'tiempo_inactivo': f"{int((now_ - datetime.fromisoformat(ultima_ts)).total_seconds())} segundos" if ultima_ts else None,
            'expira_en': f"{int(session.get_expiry_age() / 60)} minutos",
        })
        return context


# ============================================
# FUNCIONES AUXILIARES DE VISTA
# ============================================

def home(request):
    """
    Vista de inicio - redirige según el rol del usuario.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Redirigir según rol
    if hasattr(request.user, 'rol'):
        if request.user.rol == 'ADMINISTRADOR':
            return redirect('dashboard_general')
        elif request.user.rol == 'GERENTE':
            return redirect('dashboard_regional')
        elif request.user.rol == 'SUPERVISOR':
            return redirect('dashboard_general')
        elif request.user.rol == 'OPERADOR':
            return redirect('despacho_listar')
        elif request.user.rol == 'MOTORISTA':
            return redirect('despacho_listar')
    
    return render(request, 'home.html', {'user': request.user})


@login_required
def session_info_view(request):
    session = request.session
    now = timezone.now()

    login_timestamp = session.get('login_timestamp')
    ultima_actividad = session.get('ultima_actividad')

    context = {
        'session_key': session.session_key,
        'login_timestamp': datetime.fromisoformat(login_timestamp).strftime('%d/%m/%Y %H:%M:%S') if login_timestamp else None,
        'ultima_actividad': datetime.fromisoformat(ultima_actividad).strftime('%d/%m/%Y %H:%M:%S') if ultima_actividad else None,
        'tiempo_sesion': str(now - datetime.fromisoformat(login_timestamp)) if login_timestamp else None,
        'tiempo_inactivo': f"{int((now - datetime.fromisoformat(ultima_actividad)).total_seconds())} segundos" if ultima_actividad else None,
        'expira_en': f"{int(session.get_expiry_age() / 60)} minutos",
    }

    return render(request, 'session_info.html', context)