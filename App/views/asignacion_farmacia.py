"""
Vistas para Asignación de Motoristas a Farmacias
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import AsignacionFarmacia, Motorista, Farmacia
from ..forms import AsignacionFarmaciaForm
from ..decorators import SupervisorOAdminMixin, RolRequiredMixin, LoginRequiredMixin


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarAsignacionesFarmaciaView(LoginRequiredMixin, ListView):
    """
    Lista de Asignaciones de Farmacias - acceso Admin/Supervisor/Gerente.
    """
    model = AsignacionFarmacia
    template_name = 'asignacion_farmacia/asignacion_farmacia_list.html'
    context_object_name = 'asignaciones'
    paginate_by = 20

    def get_queryset(self):
        # Si es motorista, solo ve sus asignaciones
        if self.request.user.rol == 'MOTORISTA':
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                return AsignacionFarmacia.objects.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                return AsignacionFarmacia.objects.none()
        
        # Si es supervisor/admin/gerente, ve todas
        return AsignacionFarmacia.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_crear'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearAsignacionFarmaciaView(RolRequiredMixin, CreateView):
    """
    Crear Asignación de Farmacia - solo Supervisor o Administrador.
    Garantiza una activa por motorista y farmacia.
    """
    model = AsignacionFarmacia
    form_class = AsignacionFarmaciaForm
    template_name = 'asignacion_farmacia/asignacion_farmacia_form.html'
    success_url = reverse_lazy('asignacion_farmacia_listar')
    roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']

    def form_valid(self, form):
        asignacion = form.save(commit=False)
        asignacion.activa = True
        asignacion.save()
        messages.success(self.request, 'Asignación de farmacia creada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la asignación de farmacia.')
        return super().form_invalid(form)


class ReemplazarAsignacionFarmaciaView(RolRequiredMixin, UpdateView):
    """
    Reemplazar Asignación de Farmacia - desactiva la actual y crea nueva.
    Solo Supervisor o Administrador.
    """
    model = AsignacionFarmacia
    form_class = AsignacionFarmaciaForm
    template_name = 'asignacion_farmacia/asignacion_farmacia_form.html'
    success_url = reverse_lazy('asignacion_farmacia_listar')
    roles_permitidos = ['ADMINISTRADOR', 'SUPERVISOR']

    def form_valid(self, form):
        motorista = self.object.motorista
        
        # Desactivar asignación anterior
        self.object.activa = False
        self.object.save()
        
        # Crear nueva asignación
        nueva_asignacion = AsignacionFarmacia(
            motorista=motorista,
            farmacia=form.cleaned_data['farmacia'],
            activa=True
        )
        nueva_asignacion.save()
        
        messages.success(self.request, 'Asignación de farmacia reemplazada exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al reemplazar la asignación de farmacia.')
        return super().form_invalid(form)


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_asignaciones_farmacia(request):
    """
    Listar asignaciones de farmacias con paginación.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Si es motorista, solo ve sus asignaciones
    if request.user.rol == 'MOTORISTA':
        try:
            motorista = Motorista.objects.get(usuario=request.user)
            asignaciones = AsignacionFarmacia.objects.filter(motorista=motorista)
        except Motorista.DoesNotExist:
            asignaciones = AsignacionFarmacia.objects.none()
    else:
        # Si es supervisor/admin/gerente, ve todas
        asignaciones = AsignacionFarmacia.objects.all()
    
    paginator = Paginator(asignaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'asignaciones': page_obj,
        'puede_crear': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'asignacion_farmacia/asignacion_farmacia_list.html', context)


def crear_asignacion_farmacia(request):
    """
    Crear una nueva asignación de farmacia.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear asignaciones de farmacia.')
        return redirect('asignacion_farmacia_listar')
    
    if request.method == 'POST':
        form = AsignacionFarmaciaForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.activa = True
            asignacion.save()
            messages.success(request, 'Asignación de farmacia creada exitosamente.')
            return redirect('asignacion_farmacia_listar')
        else:
            messages.error(request, 'Error al crear la asignación de farmacia.')
    else:
        form = AsignacionFarmaciaForm()
    
    return render(request, 'asignacion_farmacia/asignacion_farmacia_form.html', {
        'form': form,
        'titulo': 'Crear Asignación de Farmacia'
    })


def reemplazar_asignacion_farmacia(request, pk):
    """
    Reemplazar una asignación de farmacia.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para reemplazar asignaciones de farmacia.')
        return redirect('asignacion_farmacia_listar')
    
    asignacion = get_object_or_404(AsignacionFarmacia, pk=pk)
    
    if request.method == 'POST':
        form = AsignacionFarmaciaForm(request.POST)
        if form.is_valid():
            motorista = asignacion.motorista
            
            # Desactivar asignación anterior
            asignacion.activa = False
            asignacion.save()
            
            # Crear nueva asignación
            nueva_asignacion = AsignacionFarmacia(
                motorista=motorista,
                farmacia=form.cleaned_data['farmacia'],
                activa=True
            )
            nueva_asignacion.save()
            
            messages.success(request, 'Asignación de farmacia reemplazada exitosamente.')
            return redirect('asignacion_farmacia_listar')
        else:
            messages.error(request, 'Error al reemplazar la asignación de farmacia.')
    else:
        form = AsignacionFarmaciaForm()
    
    return render(request, 'asignacion_farmacia/asignacion_farmacia_form.html', {
        'form': form,
        'titulo': 'Reemplazar Asignación de Farmacia',
        'asignacion': asignacion
    })
