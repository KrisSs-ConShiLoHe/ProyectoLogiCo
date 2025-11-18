"""
Vistas CRUD para Motos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Moto
from ..forms import MotoForm
from ..decorators import SupervisorOAdminMixin, LoginRequiredMixin


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarMotosView(LoginRequiredMixin, ListView):
    """
    Lista de Motos - acceso a todos, pero solo Admin/Supervisor pueden editar.
    """
    model = Moto
    template_name = 'moto/moto_list.html'
    context_object_name = 'motos'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearMotoView(SupervisorOAdminMixin, CreateView):
    """
    Crear Moto - solo Supervisor o Administrador.
    """
    model = Moto
    form_class = MotoForm
    template_name = 'moto/moto_form.html'
    success_url = reverse_lazy('moto_listar')

    def form_valid(self, form):
        messages.success(self.request, 'Moto creada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la moto.')
        return super().form_invalid(form)


class ModificarMotoView(SupervisorOAdminMixin, UpdateView):
    """
    Modificar Moto - solo Supervisor o Administrador.
    """
    model = Moto
    form_class = MotoForm
    template_name = 'moto/moto_form.html'
    success_url = reverse_lazy('moto_listar')

    def form_valid(self, form):
        messages.success(self.request, 'Moto modificada exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar la moto.')
        return super().form_invalid(form)


class EliminarMotoView(SupervisorOAdminMixin, DeleteView):
    """
    Eliminar Moto - solo Supervisor o Administrador.
    """
    model = Moto
    template_name = 'moto/moto_confirm_delete.html'
    success_url = reverse_lazy('moto_listar')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Moto eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_motos(request):
    """
    Listar todas las motos con paginación.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    motos = Moto.objects.all()
    paginator = Paginator(motos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'motos': page_obj,
        'puede_editar': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'moto/moto_list.html', context)


def crear_moto(request):
    """
    Crear una nueva moto.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear motos.')
        return redirect('moto_listar')
    
    if request.method == 'POST':
        form = MotoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto creada exitosamente.')
            return redirect('moto_listar')
        else:
            messages.error(request, 'Error al crear la moto.')
    else:
        form = MotoForm()
    
    return render(request, 'moto/moto_form.html', {'form': form, 'titulo': 'Crear Moto'})


def editar_moto(request, pk):
    """
    Editar una moto existente.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para editar motos.')
        return redirect('moto_listar')
    
    moto = get_object_or_404(Moto, pk=pk)
    
    if request.method == 'POST':
        form = MotoForm(request.POST, instance=moto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto modificada exitosamente.')
            return redirect('moto_listar')
        else:
            messages.error(request, 'Error al modificar la moto.')
    else:
        form = MotoForm(instance=moto)
    
    return render(request, 'moto/moto_form.html', {
        'form': form,
        'titulo': 'Editar Moto',
        'moto': moto
    })


def eliminar_moto(request, pk):
    """
    Eliminar una moto.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para eliminar motos.')
        return redirect('moto_listar')
    
    moto = get_object_or_404(Moto, pk=pk)
    
    if request.method == 'POST':
        moto.delete()
        messages.success(request, 'Moto eliminada exitosamente.')
        return redirect('moto_listar')
    
    return render(request, 'moto/moto_confirm_delete.html', {'moto': moto})
