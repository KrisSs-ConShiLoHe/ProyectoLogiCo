"""
Vistas para Asignación de Motos a Motoristas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import AsignacionMoto, Motorista, Moto
from ..forms import AsignacionMotoForm
from ..decorators import SupervisorOAdminMixin, RolRequiredMixin, LoginRequiredMixin


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarAsignacionesMotoView(LoginRequiredMixin, ListView):
    """
    Lista de Asignaciones de Motos - acceso Admin/Supervisor/Gerente, solo visualiza.
    """
    model = AsignacionMoto
    template_name = 'asignacion_moto/asignacion_moto_list.html'
    context_object_name = 'asignaciones'
    paginate_by = 20

    def get_queryset(self):
        # Si es motorista, solo ve sus asignaciones
        if self.request.user.rol == 'MOTORISTA':
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                return AsignacionMoto.objects.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                return AsignacionMoto.objects.none()
        
        # Si es supervisor/admin/gerente, ve todas
        return AsignacionMoto.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_crear'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearAsignacionMotoView(RolRequiredMixin, CreateView):
    """
    Crear Asignación de Moto - solo Supervisor o Administrador.
    Garantiza una sola asignación activa por motorista y moto disponible.
    """
    model = AsignacionMoto
    form_class = AsignacionMotoForm
    template_name = 'asignacion_moto/asignacion_moto_form.html'
    success_url = reverse_lazy('asignacion_moto_listar')
    roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Filtrar solo motos disponibles
        kwargs['motos_disponibles'] = Moto.objects.filter(disponible=True)
        return kwargs

    def form_valid(self, form):
        asignacion = form.save(commit=False)
        asignacion.activa = True
        asignacion.save()
        messages.success(self.request, 'Asignación de moto creada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la asignación de moto.')
        return super().form_invalid(form)


class ReemplazarAsignacionMotoView(RolRequiredMixin, UpdateView):
    """
    Reemplazar Asignación de Moto - desactiva la actual y crea nueva.
    Solo Supervisor o Administrador.
    """
    model = AsignacionMoto
    form_class = AsignacionMotoForm
    template_name = 'asignacion_moto/asignacion_moto_form.html'
    success_url = reverse_lazy('asignacion_moto_listar')
    roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']

    def form_valid(self, form):
        motorista = self.object.motorista
        
        # Desactivar asignación anterior
        self.object.activa = False
        self.object.save()
        
        # Crear nueva asignación
        nueva_asignacion = AsignacionMoto(
            motorista=motorista,
            moto=form.cleaned_data['moto'],
            activa=True
        )
        nueva_asignacion.save()
        
        messages.success(self.request, 'Asignación de moto reemplazada exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al reemplazar la asignación de moto.')
        return super().form_invalid(form)


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_asignaciones_moto(request):
    """
    Listar asignaciones de motos con paginación.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Si es motorista, solo ve sus asignaciones
    if request.user.rol == 'MOTORISTA':
        try:
            motorista = Motorista.objects.get(usuario=request.user)
            asignaciones = AsignacionMoto.objects.filter(motorista=motorista)
        except Motorista.DoesNotExist:
            asignaciones = AsignacionMoto.objects.none()
    else:
        # Si es supervisor/admin/gerente, ve todas
        asignaciones = AsignacionMoto.objects.all()
    
    paginator = Paginator(asignaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'asignaciones': page_obj,
        'puede_crear': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'asignacion_moto/asignacion_moto_list.html', context)


def crear_asignacion_moto(request):
    """
    Crear una nueva asignación de moto.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear asignaciones de moto.')
        return redirect('asignacion_moto_listar')
    
    if request.method == 'POST':
        form = AsignacionMotoForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.activa = True
            asignacion.save()
            messages.success(request, 'Asignación de moto creada exitosamente.')
            return redirect('asignacion_moto_listar')
        else:
            messages.error(request, 'Error al crear la asignación de moto.')
    else:
        # Solo mostrar motos disponibles
        form = AsignacionMotoForm()
        form.fields['moto'].queryset = Moto.objects.filter(disponible=True)
    
    return render(request, 'asignacion_moto/asignacion_moto_form.html', {
        'form': form,
        'titulo': 'Crear Asignación de Moto'
    })


def reemplazar_asignacion_moto(request, pk):
    """
    Reemplazar una asignación de moto.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para reemplazar asignaciones de moto.')
        return redirect('asignacion_moto_listar')
    
    asignacion = get_object_or_404(AsignacionMoto, pk=pk)
    
    if request.method == 'POST':
        form = AsignacionMotoForm(request.POST)
        if form.is_valid():
            motorista = asignacion.motorista
            
            # Desactivar asignación anterior
            asignacion.activa = False
            asignacion.save()
            
            # Crear nueva asignación
            nueva_asignacion = AsignacionMoto(
                motorista=motorista,
                moto=form.cleaned_data['moto'],
                activa=True
            )
            nueva_asignacion.save()
            
            messages.success(request, 'Asignación de moto reemplazada exitosamente.')
            return redirect('asignacion_moto_listar')
        else:
            messages.error(request, 'Error al reemplazar la asignación de moto.')
    else:
        form = AsignacionMotoForm()
        form.fields['moto'].queryset = Moto.objects.filter(disponible=True)
    
    return render(request, 'asignacion_moto/asignacion_moto_form.html', {
        'form': form,
        'titulo': 'Reemplazar Asignación de Moto',
        'asignacion': asignacion
    })
