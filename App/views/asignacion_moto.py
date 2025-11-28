"""
Vistas para Asignación de Motos a Motoristas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import AsignacionMoto, Motorista, Moto
from ..forms import AsignacionMotoForm
from ..decorators import SupervisorOAdminMixin, RolRequiredMixin, LoginRequiredMixin
import django_filters
from django_filters.views import FilterView
from django.db.models import Q




# ============================================
# VISTAS BASADAS EN CLASES
# ============================================


class AsignacionMotoFilter(django_filters.FilterSet):
    motorista = django_filters.ModelChoiceFilter(queryset=Motorista.objects.all())
    moto = django_filters.ModelChoiceFilter(queryset=Moto.objects.all())
    fecha_asignacion = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AsignacionMoto
        fields = ['motorista', 'moto', 'fecha_asignacion']


class ListarAsignacionesMotoView(LoginRequiredMixin, ListView):
    """
    Lista de Asignaciones de Motos - acceso Admin/Supervisor/Gerente, solo visualiza.
    """
    model = AsignacionMoto
    filterset_class = AsignacionMotoFilter
    template_name = 'asignacion_moto/asignacion_moto_list.html'
    context_object_name = 'asignaciones'
    paginate_by = 20

    asignaciones = AsignacionMoto.objects.all().order_by('-fecha_asignacion')

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
    template_name = 'asignacion_moto/asignacion_form.html'
    success_url = reverse_lazy('asignacion_moto_listar')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
            messages.error(request, 'No tienes permiso para crear asignaciones.')
            return redirect('asignacion_moto_listar')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs  # Form generará los recursos libres automáticamente

    def form_valid(self, form):
        messages.success(self.request, 'Asignación creada exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la asignación.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Asignación'
        return context


class ReemplazarAsignacionMotoView(RolRequiredMixin, UpdateView):
    """
    Reemplazar Asignación de Moto - desactiva la actual y crea nueva.
    Solo Supervisor o Administrador.
    """
    model = AsignacionMoto
    form_class = AsignacionMotoForm
    template_name = 'asignacion_moto/asignacion_form.html'
    success_url = reverse_lazy('asignacion_moto_listar')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
            messages.error(request, 'No tienes permiso para editar asignaciones.')
            return redirect('asignacion_moto_listar')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Asignación modificada exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar la asignación.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Asignación'
        context['asignacion'] = self.object
        return context
    

# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_asignaciones_moto(request):

    if not request.user.is_authenticated:
        return redirect('login')

    # Obtener valores GET
    id_motorista = request.GET.get("id_motorista")
    motorista = request.GET.get("motorista")
    id_moto = request.GET.get("id_moto")
    moto = request.GET.get("moto")
    fecha_asignacion = request.GET.get("fecha_asignacion")
    fecha_desasignacion = request.GET.get("fecha_desasignacion")
    activa = request.GET.get("activa")

    qs = AsignacionMoto.objects.select_related("motorista", "moto").all()

    # Filtros correctos para FK
    if id_motorista:
        qs = qs.filter(motorista__identificador_unico__icontains=id_motorista)

    if motorista:
        qs = qs.filter(
            Q(motorista__usuario__first_name__icontains=motorista) |
            Q(motorista__usuario__last_name__icontains=motorista) |
            Q(motorista__rut__icontains=motorista)
        )

    if id_moto:
        qs = qs.filter(moto__identificador_unico__icontains=id_moto)

    if moto:
        qs = qs.filter(
            Q(moto__patente__icontains=moto) |
            Q(moto__marca__icontains=moto) |
            Q(moto__modelo__icontains=moto)
        )

    if fecha_asignacion:
        qs = qs.filter(fecha_asignacion=fecha_asignacion)

    if fecha_desasignacion:
        qs = qs.filter(fecha_desasignacion=fecha_desasignacion)

    if activa == "true":
        qs = qs.filter(activa=True)
    elif activa == "false":
        qs = qs.filter(activa=False)

    # Paginación
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "a_m": page_obj,
        "is_paginated": paginator.num_pages > 1,
        "puede_crear": request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR'],
    }
    return render(request, "asignacion_moto/asignacion_moto_list.html", context)


def crear_asignacion_moto(request):
    """
    Crear una nueva asignación moto-motorista
    """
    
    # Verificar permisos
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear asignaciones.')
        return redirect('asignacion_moto_listar')
    
    if request.method == 'POST':
        form = AsignacionMotoForm(request.POST)  # ← Sin parámetros extra
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignación creada exitosamente.')
            return redirect('asignacion_moto_listar')
        else:
            messages.error(request, 'Error al crear la asignación.')
    else:
        form = AsignacionMotoForm()  # ← Sin parámetros extra
    
    return render(request, 'asignacion_moto/asignacion_moto_form.html', {
        'form': form,
        'titulo': 'Crear Asignación'
    })


def reemplazar_asignacion_moto(request, pk):
    """
    Reemplazar una asignación de moto.
    """
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para editar asignaciones.')
        return redirect('asignacion_moto_listar')
    asignacion = get_object_or_404(AsignacionMoto, pk=pk)
    if request.method == 'POST':
        form = AsignacionMotoForm(request.POST, asignacion_actual=asignacion)  # Sin instance, pero con asignacion_actual para querysets
        if form.is_valid():
            # Desactiva la actual (histórico)
            asignacion.activa = False
            asignacion.save()  # Esto guarda la asignación anterior como inactiva con fecha_desasignacion y libera recursos
            # Crea nueva asignación manualmente con los datos del form
            nueva = AsignacionMoto(
                motorista=form.cleaned_data['motorista'],
                moto=form.cleaned_data['moto'],
                activa=True
            )
            nueva.save()  # Esto guarda la nueva asignación y maneja la lógica de desactivar otras y actualizar estados
            return redirect('asignacion_moto_listar')
    else:
        form = AsignacionMotoForm(instance=asignacion, asignacion_actual=asignacion)  # Con instance para valores iniciales y asignacion_actual para querysets
    return render(request, 'asignacion_moto/asignacion_moto_form.html', {'form': form, 'asignacion': asignacion})

    
    # asignacion = get_object_or_404(AsignacionMoto, pk=pk)
    
    # if request.method == 'POST':
    #     form = AsignacionMotoForm(request.POST, instance=asignacion)  # ← Solo instance
        
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'Asignación modificada exitosamente.')
    #         return redirect('asignacion_moto_listar')
    #     else:
    #         messages.error(request, 'Error al modificar la asignación.')
    # else:
    #     form = AsignacionMotoForm(instance=asignacion)  # ← Solo instance
    
    # return render(request, 'asignacion_moto/asignacion_moto_form.html', {
    #     'form': form,
    #     'titulo': 'Editar Asignación',
    #     'asignacion': asignacion
    # })