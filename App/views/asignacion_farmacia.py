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
import django_filters
from django_filters.views import FilterView
from django.db.models import Q


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================


class AsignacionFarmaciaFilter(django_filters.FilterSet):
    motorista = django_filters.ModelChoiceFilter(queryset=Motorista.objects.all())
    farmacia = django_filters.ModelChoiceFilter(queryset=Farmacia.objects.all())
    fecha_asignacion = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AsignacionFarmacia
        fields = ['motorista', 'farmacia', 'fecha_asignacion']
        

class ListarAsignacionesFarmaciaView(LoginRequiredMixin, ListView):
    """
    Lista de Asignaciones de Farmacias - acceso Admin/Supervisor/Gerente.
    """
    model = AsignacionFarmacia
    filterset_class = AsignacionFarmaciaFilter
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

    id_motorista = request.GET.get("id_motorista")
    motorista = request.GET.get("motorista")
    id_farmacia = request.GET.get("id_farmacia")
    farmacia = request.GET.get("farmacia")
    fecha_asignacion = request.GET.get("fecha_asignacion")
    fecha_desasignacion = request.GET.get("fecha_desasignacion")
    activa = request.GET.get("activa")

    qs = AsignacionFarmacia.objects.select_related("motorista", "farmacia").all()

    # Buscar motorista por nombre, apellido, rut o ID

    if id_motorista:
        qs = qs.filter(motorista__identificador_unico__icontains=id_motorista)

    if motorista:
        qs = qs.filter(
            Q(motorista__usuario__first_name__icontains=motorista) |
            Q(motorista__usuario__last_name__icontains=motorista) |
            Q(motorista__rut__icontains=motorista)
        )

    if id_farmacia:
        qs = qs.filter(farmacia__identificador_unico__icontains=id_farmacia)

    # Nombre de la farmacia
    if farmacia:
        qs = qs.filter(farmacia__nombre__icontains=farmacia)

    # Fechas
    if fecha_asignacion:
        qs = qs.filter(fecha_asignacion=fecha_asignacion)

    if fecha_desasignacion:
        qs = qs.filter(fecha_desasignacion=fecha_desasignacion)

    if activa == "true":
        qs = qs.filter(activa=True)
    elif activa == "false":
        qs = qs.filter(activa=False)

    # --- PAGINACIÓN ---
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "asignacion_farmacia/asignacion_farmacia_list.html",
        {
            "page_obj": page_obj,
            "puede_crear": request.user.rol in ["ADMINISTRADOR", "SUPERVISOR"]
        },
    )


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
        form = AsignacionFarmaciaForm(request.POST, asignacion_actual=asignacion)  # Sin instance, pero con asignacion_actual para querysets
        if form.is_valid():
            # Desactiva la actual (histórico)
            asignacion.activa = False
            asignacion.save()  # Esto guarda la asignación anterior como inactiva con fecha_desasignacion y libera recursos
            # Crea nueva asignación manualmente con los datos del form
            nueva = AsignacionFarmacia(
                motorista=form.cleaned_data['motorista'],
                farmacia=form.cleaned_data['farmacia'],
                activa=True
            )
            nueva.save()  # Esto guarda la nueva asignación y maneja la lógica de desactivar otras y actualizar estados
            messages.success(request, 'Asignación de farmacia reemplazada exitosamente.')
            return redirect('asignacion_farmacia_listar')
        else:
            messages.error(request, 'Error al reemplazar la asignación de farmacia.')
    else:
        form = AsignacionFarmaciaForm(instance=asignacion, asignacion_actual=asignacion)  # Con instance para valores iniciales y asignacion_actual para querysets
    
    return render(request, 'asignacion_farmacia/asignacion_farmacia_form.html', {
        'form': form,
        'titulo': 'Reemplazar Asignación de Farmacia',
        'asignacion': asignacion
    })
