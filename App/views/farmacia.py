"""
Vistas CRUD para Farmacias
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Farmacia
from ..forms import FarmaciaForm
from ..decorators import SupervisorOAdminMixin, RolRequiredMixin, LoginRequiredMixin
import django_filters
from django_filters.views import FilterView


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarFarmaciasView(LoginRequiredMixin, ListView):
    """
    Lista de Farmacias - acceso a todos, pero solo Admin/Supervisor pueden editar.
    """
    model = Farmacia
    template_name = 'farmacia/farmacia_list.html'
    context_object_name = 'farmacias'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearFarmaciaView(SupervisorOAdminMixin, CreateView):
    """
    Crear Farmacia - solo Supervisor o Administrador.
    """
    model = Farmacia
    form_class = FarmaciaForm
    template_name = 'farmacia/farmacia_form.html'
    success_url = reverse_lazy('farmacia_listar')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.request.FILES:
            self.object.imagen = self.request.FILES.get('imagen')
        self.object.save()
        messages.success(self.request, 'Farmacia creada/modificada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la farmacia.')
        return super().form_invalid(form)


class ModificarFarmaciaView(SupervisorOAdminMixin, UpdateView):
    """
    Modificar Farmacia - solo Supervisor o Administrador.
    """
    model = Farmacia
    form_class = FarmaciaForm
    template_name = 'farmacia/farmacia_form.html'
    success_url = reverse_lazy('farmacia_listar')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.request.FILES:
            self.object.imagen = self.request.FILES.get('imagen')
        self.object.save()
        messages.success(self.request, 'Farmacia creada/modificada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar la farmacia.')
        return super().form_invalid(form)


class EliminarFarmaciaView(SupervisorOAdminMixin, DeleteView):
    """
    Eliminar Farmacia - solo Supervisor o Administrador.
    """
    model = Farmacia
    template_name = 'farmacia/farmacia_confirm_delete.html'
    success_url = reverse_lazy('farmacia_listar')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Farmacia eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    

class FarmaciaDetailView(LoginRequiredMixin, DetailView):
    model = Farmacia
    template_name = 'farmacia/farmacia_detail.html'
    context_object_name = 'farmacia'


class FarmaciaFilter(django_filters.FilterSet):
    identificador_unico = django_filters.CharFilter(lookup_expr='icontains')
    comuna = django_filters.CharFilter(lookup_expr='icontains')
    region = django_filters.CharFilter(lookup_expr='icontains')
    horario_recepcion_inicio = django_filters.CharFilter(lookup_expr='icontains')
    horario_recepcion_fin = django_filters.CharFilter(lookup_expr='icontains')
    dias_operativos = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Farmacia
        fields = ['identificador_unico', 'region', 'comuna', 'horario_recepcion_inicio', 'horario_recepcion_fin', 'dias_operativos']


class FarmaciaListFilterView(LoginRequiredMixin, FilterView):
    model = Farmacia
    template_name = 'farmacia/farmacia_list.html'
    filterset_class = FarmaciaFilter
    context_object_name = 'farmacias'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


# ============================================
# VISTAS BASADAS EN FUNCIONES (ALTERNATIVA)
# ============================================

def listar_farmacias(request):
    """
    Listar todas las farmacias con paginación.
    """
    query_id = request.GET.get('identificador_unico')
    query_nombre = request.GET.get('nombre')
    query_region = request.GET.get('region')
    query_comuna = request.GET.get('comuna')
    query_horario_inicio = request.GET.get('horario_recepcion_inicio')
    query_horario_fin = request.GET.get('horario_recepcion_fin')
    query_dias = request.GET.get('dias_operativos')

    if not request.user.is_authenticated:
        return redirect('login')

    qs = Farmacia.objects.all()
    if query_id: qs = qs.filter(identificador_unico__icontains=query_id)
    if query_nombre: qs = qs.filter(nombre__icontains=query_nombre)
    if query_region: qs = qs.filter(region__icontains=query_region)
    if query_comuna: qs = qs.filter(comuna__icontains=query_comuna)
    if query_horario_inicio: qs = qs.filter(horario_recepcion_inicio__icontains=query_horario_inicio)
    if query_horario_fin: qs = qs.filter(horario_recepcion_fin__icontains=query_horario_fin)
    if query_dias: qs = qs.filter(dias_operativos__icontains=query_dias)
    
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'farmacias': page_obj,  # ← Cambio aquí
        'is_paginated': paginator.num_pages > 1,  # ← Añadir esto
        'puede_editar': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'farmacia/farmacia_list.html', context)


def crear_farmacia(request):
    """
    Crear una nueva farmacia.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear farmacias.')
        return redirect('farmacia_listar')
    
    if request.method == 'POST':
        form = FarmaciaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farmacia creada exitosamente.')
            return redirect('farmacia_listar')
        else:
            messages.error(request, 'Error al crear la farmacia.')
    else:
        form = FarmaciaForm()
    
    return render(request, 'farmacia/farmacia_form.html', {'form': form, 'titulo': 'Crear Farmacia'})


def editar_farmacia(request, pk):
    """
    Editar una farmacia existente.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para editar farmacias.')
        return redirect('farmacia_listar')
    
    farmacia = get_object_or_404(Farmacia, pk=pk)
    
    if request.method == 'POST':
        form = FarmaciaForm(request.POST, request.FILES, instance=farmacia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farmacia modificada exitosamente.')
            return redirect('farmacia_listar')
        else:
            messages.error(request, 'Error al modificar la farmacia.')
    else:
        form = FarmaciaForm(instance=farmacia)
    
    return render(request, 'farmacia/farmacia_form.html', {
        'form': form,
        'titulo': 'Editar Farmacia',
        'farmacia': farmacia
    })


def eliminar_farmacia(request, pk):
    """
    Eliminar una farmacia.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para eliminar farmacias.')
        return redirect('farmacia_listar')
    
    farmacia = get_object_or_404(Farmacia, pk=pk)
    
    if request.method == 'POST':
        farmacia.delete()
        messages.success(request, 'Farmacia eliminada exitosamente.')
        return redirect('farmacia_listar')
    
    return render(request, 'farmacia/farmacia_confirm_delete.html', {'farmacia': farmacia})
