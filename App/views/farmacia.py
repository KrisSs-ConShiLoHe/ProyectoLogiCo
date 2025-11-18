"""
Vistas CRUD para Farmacias
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Farmacia
from ..forms import FarmaciaForm
from ..decorators import SupervisorOAdminMixin, RolRequiredMixin, LoginRequiredMixin


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
        messages.success(self.request, 'Farmacia creada exitosamente.')
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
        messages.success(self.request, 'Farmacia modificada exitosamente.')
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


# ============================================
# VISTAS BASADAS EN FUNCIONES (ALTERNATIVA)
# ============================================

def listar_farmacias(request):
    """
    Listar todas las farmacias con paginación.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    farmacias = Farmacia.objects.all()
    paginator = Paginator(farmacias, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'farmacias': page_obj,
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
        form = FarmaciaForm(request.POST)
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
        form = FarmaciaForm(request.POST, instance=farmacia)
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
