"""
Vistas CRUD para Motoristas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Motorista
from ..forms import MotoristaForm
from ..decorators import SupervisorOAdminMixin, LoginRequiredMixin


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarMotoristasView(LoginRequiredMixin, ListView):
    """
    Lista de Motoristas - acceso a todos, pero solo Admin/Supervisor pueden editar.
    """
    model = Motorista
    template_name = 'motorista/motorista_list.html'
    context_object_name = 'motoristas'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearMotoristaView(SupervisorOAdminMixin, CreateView):
    """
    Crear Motorista - solo Supervisor o Administrador.
    """
    model = Motorista
    form_class = MotoristaForm
    template_name = 'motorista/motorista_form.html'
    success_url = reverse_lazy('motorista_listar')

    def form_valid(self, form):
        messages.success(self.request, 'Motorista creado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el motorista.')
        return super().form_invalid(form)


class ModificarMotoristaView(SupervisorOAdminMixin, UpdateView):
    """
    Modificar Motorista - solo Supervisor o Administrador.
    """
    model = Motorista
    form_class = MotoristaForm
    template_name = 'motorista/motorista_form.html'
    success_url = reverse_lazy('motorista_listar')

    def form_valid(self, form):
        messages.success(self.request, 'Motorista modificado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar el motorista.')
        return super().form_invalid(form)


class EliminarMotoristaView(SupervisorOAdminMixin, DeleteView):
    """
    Eliminar Motorista - solo Supervisor o Administrador.
    """
    model = Motorista
    template_name = 'motorista/motorista_confirm_delete.html'
    success_url = reverse_lazy('motorista_listar')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Motorista eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_motoristas(request):
    """
    Listar todos los motoristas con paginación.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    motoristas = Motorista.objects.all()
    paginator = Paginator(motoristas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'motoristas': page_obj,
        'puede_editar': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'motorista/motorista_list.html', context)


def crear_motorista(request):
    """
    Crear un nuevo motorista.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear motoristas.')
        return redirect('motorista_listar')
    
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista creado exitosamente.')
            return redirect('motorista_listar')
        else:
            messages.error(request, 'Error al crear el motorista.')
    else:
        form = MotoristaForm()
    
    return render(request, 'motorista/motorista_form.html', {'form': form, 'titulo': 'Crear Motorista'})


def editar_motorista(request, pk):
    """
    Editar un motorista existente.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para editar motoristas.')
        return redirect('motorista_listar')
    
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista modificado exitosamente.')
            return redirect('motorista_listar')
        else:
            messages.error(request, 'Error al modificar el motorista.')
    else:
        form = MotoristaForm(instance=motorista)
    
    return render(request, 'motorista/motorista_form.html', {
        'form': form,
        'titulo': 'Editar Motorista',
        'motorista': motorista
    })


def eliminar_motorista(request, pk):
    """
    Eliminar un motorista.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para eliminar motoristas.')
        return redirect('motorista_listar')
    
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        motorista.delete()
        messages.success(request, 'Motorista eliminado exitosamente.')
        return redirect('motorista_listar')
    
    return render(request, 'motorista/motorista_confirm_delete.html', {'motorista': motorista})
