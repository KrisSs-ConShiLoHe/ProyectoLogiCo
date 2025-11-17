# roles.py
"""
Sistema de roles y permisos para LogiCo
Define qué puede hacer cada tipo de usuario
"""

# Definición de roles disponibles
ROLES = {
    'admin': 'Administrador',
    'supervisor': 'Supervisor',
    'motorista': 'Motorista',
    'farmacia': 'Farmacia',
}

# Permisos por rol
PERMISOS_POR_ROL = {
    'admin': {
        'farmacias': ['view', 'add', 'change', 'delete'],
        'motoristas': ['view', 'add', 'change', 'delete'],
        'motos': ['view', 'add', 'change', 'delete'],
        'asignaciones': ['view', 'add', 'change', 'delete'],
        'usuarios': ['view', 'add', 'change', 'delete'],
        'reportes': ['view'],
        'configuracion': ['view', 'change'],
    },
    'supervisor': {
        'farmacias': ['view'],
        'motoristas': ['view', 'add', 'change'],
        'motos': ['view', 'add', 'change'],
        'asignaciones': ['view', 'add', 'change'],
        'usuarios': ['view'],
        'reportes': ['view'],
        'configuracion': [],
    },
    'motorista': {
        'farmacias': [],
        'motoristas': [],  # Solo puede ver su propio perfil
        'motos': [],  # Solo puede ver su moto asignada
        'asignaciones': [],  # Solo puede ver sus asignaciones
        'usuarios': [],
        'reportes': [],
        'configuracion': [],
    },
    'farmacia': {
        'farmacias': [],  # Solo puede ver su farmacia
        'motoristas': ['view'],  # Solo motoristas de su farmacia
        'motos': ['view'],
        'asignaciones': ['view'],
        'usuarios': [],
        'reportes': ['view'],
        'configuracion': [],
    },
}

# Mapeo de módulos a nombres legibles
MODULOS = {
    'farmacias': 'Farmacias',
    'motoristas': 'Motoristas',
    'motos': 'Motos',
    'asignaciones': 'Asignaciones',
    'usuarios': 'Usuarios',
    'reportes': 'Reportes',
    'configuracion': 'Configuración',
}

def obtener_rol_usuario(user):
    """Obtiene el rol principal del usuario"""
    if user.is_superuser or user.is_staff:
        return 'admin'
    
    if user.groups.exists():
        return user.groups.first().name
    
    return None

def tiene_permiso(user, modulo, accion):
    """
    Verifica si un usuario tiene permiso para una acción en un módulo
    
    Args:
        user: Usuario a verificar
        modulo: Módulo (farmacias, motoristas, etc)
        accion: Acción (view, add, change, delete)
    
    Returns:
        bool: True si tiene permiso, False si no
    """
    rol = obtener_rol_usuario(user)
    
    if not rol:
        return False
    
    permisos = PERMISOS_POR_ROL.get(rol, {})
    modulo_permisos = permisos.get(modulo, [])
    
    return accion in modulo_permisos

def obtener_permisos_usuario(user):
    """Obtiene todos los permisos del usuario"""
    rol = obtener_rol_usuario(user)
    
    if not rol:
        return {}
    
    return PERMISOS_POR_ROL.get(rol, {})