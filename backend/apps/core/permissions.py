"""
Sistema de permissões baseado em funções de negócio para o sistema de tintas.
Implementa controle de acesso granular baseado nos roles definidos no modelo User.
"""

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from enum import Enum


class BusinessRole(Enum):
    """
    Enumeração dos roles de negócio do sistema
    """
    ADMIN = 'administrador'
    VENDOR = 'vendedor'  
    OPERATOR = 'operador'
    VIEWER = 'visualizador'


class BusinessPermissions:
    """
    Classe base para definir permissões de negócio
    """
    
    # Mapeamento entre roles e permissões do modelo User
    ROLE_PERMISSIONS_MAP = {
        BusinessRole.ADMIN: ['pode_administrar'],
        BusinessRole.VENDOR: ['pode_vender'],
        BusinessRole.OPERATOR: ['pode_gerenciar_estoque'],
        BusinessRole.VIEWER: [],  # Apenas visualização
    }
    
    # Hierarquia de permissões (roles superiores incluem permissões dos inferiores)
    ROLE_HIERARCHY = {
        BusinessRole.ADMIN: [BusinessRole.ADMIN, BusinessRole.VENDOR, BusinessRole.OPERATOR, BusinessRole.VIEWER],
        BusinessRole.VENDOR: [BusinessRole.VENDOR, BusinessRole.VIEWER],
        BusinessRole.OPERATOR: [BusinessRole.OPERATOR, BusinessRole.VIEWER],
        BusinessRole.VIEWER: [BusinessRole.VIEWER],
    }
    
    @staticmethod
    def user_has_role(user, role: BusinessRole) -> bool:
        """
        Verifica se um usuário possui um role específico
        """
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return False
            
        if not user.ativo:
            return False
            
        # Superuser sempre tem todas as permissões
        if user.is_superuser:
            return True
            
        # Verifica role específico
        if role == BusinessRole.ADMIN:
            return user.pode_administrar
        elif role == BusinessRole.VENDOR:
            return user.pode_vender
        elif role == BusinessRole.OPERATOR:
            return user.pode_gerenciar_estoque
        elif role == BusinessRole.VIEWER:
            # Todo usuário autenticado e ativo pode visualizar
            return True
            
        return False
    
    @staticmethod 
    def user_has_any_role(user, roles: list) -> bool:
        """
        Verifica se o usuário possui pelo menos um dos roles da lista
        """
        for role in roles:
            if BusinessPermissions.user_has_role(user, role):
                return True
        return False
    
    @staticmethod
    def get_user_roles(user) -> list:
        """
        Retorna lista de roles que o usuário possui
        """
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            return []
            
        if not user.ativo:
            return []
            
        roles = []
        
        # Superuser tem todos os roles
        if user.is_superuser:
            return list(BusinessRole)
            
        # Verifica cada role
        if user.pode_administrar:
            roles.append(BusinessRole.ADMIN)
        if user.pode_vender:
            roles.append(BusinessRole.VENDOR)  
        if user.pode_gerenciar_estoque:
            roles.append(BusinessRole.OPERATOR)
            
        # Todo usuário ativo pode visualizar
        if not roles:  # Se não tem nenhum role específico
            roles.append(BusinessRole.VIEWER)
            
        return roles


class IsAuthenticated(permissions.BasePermission):
    """
    Permissão básica: usuário deve estar autenticado e ativo
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'ativo', True)
        )


class IsAdministrator(permissions.BasePermission):
    """
    Permissão para administradores do sistema
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN)


class IsVendor(permissions.BasePermission):
    """
    Permissão para funcionários que podem realizar vendas
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_role(request.user, BusinessRole.VENDOR)


class IsOperator(permissions.BasePermission):
    """
    Permissão para operadores que podem gerenciar estoque
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_role(request.user, BusinessRole.OPERATOR)


class HasStoreAccess(permissions.BasePermission):
    """
    Permissão para verificar acesso específico à loja
    """
    
    def has_permission(self, request, view):
        if not BusinessPermissions.user_has_role(request.user, BusinessRole.VIEWER):
            return False
            
        # Administradores têm acesso a todas as lojas
        if BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN):
            return True
            
        # Se há um parâmetro de loja na view, verifica permissão específica
        loja_id = getattr(view, 'loja_id', None) or request.data.get('loja_id')
        if loja_id:
            return self._check_store_permission(request.user, loja_id)
            
        return True
    
    def _check_store_permission(self, user, loja_id):
        """Verifica permissão específica para uma loja"""
        try:
            from apps.companies.models import UsuarioLoja, Loja
            loja = Loja.objects.get(id=loja_id)
            usuario_loja = UsuarioLoja.objects.get(
                usuario=user, 
                loja=loja, 
                ativo=True
            )
            return True
        except (UsuarioLoja.DoesNotExist, Loja.DoesNotExist):
            return False


class CanManageInventory(permissions.BasePermission):
    """
    Permissão específica para gerenciamento de estoque
    """
    
    def has_permission(self, request, view):
        return (
            BusinessPermissions.user_has_role(request.user, BusinessRole.OPERATOR) or
            BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN)
        )


class CanSell(permissions.BasePermission):
    """
    Permissão específica para realizar vendas
    """
    
    def has_permission(self, request, view):
        return (
            BusinessPermissions.user_has_role(request.user, BusinessRole.VENDOR) or
            BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN)
        )


class CanAccessFinancial(permissions.BasePermission):
    """
    Permissão para acessar informações financeiras
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'ativo', True) and
            (getattr(request.user, 'pode_acessar_financeiro', False) or
             BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN))
        )


# Decorators para função-based views
from functools import wraps
from django.http import HttpResponseForbidden


def require_role(*roles):
    """
    Decorator que exige um ou mais roles específicos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not BusinessPermissions.user_has_any_role(request.user, roles):
                return HttpResponseForbidden("Permissão negada: role insuficiente")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_store_access(loja_param='loja_id'):
    """
    Decorator que exige acesso específico a uma loja
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            loja_id = kwargs.get(loja_param) or request.GET.get(loja_param)
            
            if loja_id and not BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN):
                has_access = HasStoreAccess()._check_store_permission(request.user, loja_id)
                if not has_access:
                    return HttpResponseForbidden("Permissão negada: sem acesso a esta loja")
                    
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class TintasBusinessPermissions:
    """
    Classe utilitária para verificações específicas do negócio de tintas
    """
    
    @staticmethod
    def can_create_tintometric_formula(user):
        """Verifica se usuário pode criar fórmulas tintométricas"""
        return BusinessPermissions.user_has_role(user, BusinessRole.OPERATOR)
    
    @staticmethod
    def can_produce_paint(user, loja=None):
        """Verifica se usuário pode produzir tintas"""
        if not (BusinessPermissions.user_has_role(user, BusinessRole.VENDOR) or
                BusinessPermissions.user_has_role(user, BusinessRole.OPERATOR)):
            return False
            
        if loja and not BusinessPermissions.user_has_role(user, BusinessRole.ADMIN):
            return HasStoreAccess()._check_store_permission(user, loja.id)
            
        return True
    
    @staticmethod
    def can_adjust_prices(user):
        """Verifica se usuário pode ajustar preços"""
        return (
            getattr(user, 'pode_acessar_financeiro', False) or
            BusinessPermissions.user_has_role(user, BusinessRole.ADMIN)
        )
    
    @staticmethod
    def can_give_discount(user, loja=None, amount=0):
        """Verifica se usuário pode dar desconto e qual o limite"""
        if not BusinessPermissions.user_has_role(user, BusinessRole.VENDOR):
            return False, 0
            
        if BusinessPermissions.user_has_role(user, BusinessRole.ADMIN):
            return True, 100  # Admin pode dar até 100% de desconto
            
        if loja:
            try:
                from apps.companies.models import UsuarioLoja
                usuario_loja = UsuarioLoja.objects.get(
                    usuario=user, 
                    loja=loja, 
                    ativo=True
                )
                if usuario_loja.pode_dar_desconto:
                    limit = usuario_loja.limite_desconto_percentual or 0
                    can_give = amount <= limit
                    return can_give, limit
            except UsuarioLoja.DoesNotExist:
                pass
                
        return False, 0


class IsViewer(permissions.BasePermission):
    """
    Permissão básica para visualização (todos os usuários ativos)
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_role(request.user, BusinessRole.VIEWER)


class CanSell(permissions.BasePermission):
    """
    Permissão para operações de venda
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_any_role(
            request.user, 
            [BusinessRole.ADMIN, BusinessRole.VENDOR]
        )


class CanManageInventory(permissions.BasePermission):
    """
    Permissão para gerenciar estoque
    """
    
    def has_permission(self, request, view):
        return BusinessPermissions.user_has_any_role(
            request.user,
            [BusinessRole.ADMIN, BusinessRole.OPERATOR]
        )


class CanAccessFinancial(permissions.BasePermission):
    """
    Permissão para acessar dados financeiros
    """
    
    def has_permission(self, request, view):
        return (
            BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN) or
            getattr(request.user, 'pode_acessar_financeiro', False)
        )


class ReadOnlyOrHasWritePermission(permissions.BasePermission):
    """
    Permissão customizada que permite leitura para visualizadores
    e escrita apenas para usuários com permissões específicas
    """
    
    def has_permission(self, request, view):
        # Permite leitura para visualizadores
        if request.method in permissions.SAFE_METHODS:
            return BusinessPermissions.user_has_role(request.user, BusinessRole.VIEWER)
        
        # Para operações de escrita, verifica permissões específicas
        return BusinessPermissions.user_has_any_role(
            request.user,
            [BusinessRole.ADMIN, BusinessRole.VENDOR, BusinessRole.OPERATOR]
        )


class OwnerOrAdminPermission(permissions.BasePermission):
    """
    Permissão que permite acesso apenas ao dono do objeto ou administrador
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Administrador pode acessar qualquer objeto
        if BusinessPermissions.user_has_role(request.user, BusinessRole.ADMIN):
            return True
            
        # Verifica se o objeto tem um campo 'user' ou 'owner'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
            
        return False


def get_permissions_for_action(action: str, resource: str) -> list:
    """
    Retorna as permissões necessárias para uma ação específica em um recurso
    
    Args:
        action: 'create', 'read', 'update', 'delete', 'list'
        resource: nome do recurso (ex: 'sale', 'product', 'user')
    
    Returns:
        Lista de classes de permissão
    """
    
    # Mapeamento de ações para recursos específicos
    permission_map = {
        # Vendas
        'sale': {
            'create': [CanSell],
            'read': [IsViewer],
            'update': [CanSell], 
            'delete': [IsAdministrator],
            'list': [IsViewer],
        },
        
        # Produtos e Estoque
        'product': {
            'create': [CanManageInventory],
            'read': [IsViewer],
            'update': [CanManageInventory],
            'delete': [IsAdministrator],
            'list': [IsViewer],
        },
        
        # Usuários 
        'user': {
            'create': [IsAdministrator],
            'read': [IsAuthenticated],
            'update': [OwnerOrAdminPermission],
            'delete': [IsAdministrator],
            'list': [IsAdministrator],
        },
        
        # Financeiro
        'financial': {
            'create': [CanAccessFinancial],
            'read': [CanAccessFinancial],
            'update': [CanAccessFinancial],
            'delete': [IsAdministrator],
            'list': [CanAccessFinancial],
        },
        
        # Configurações
        'configuration': {
            'create': [IsAdministrator],
            'read': [IsAuthenticated],
            'update': [IsAdministrator],
            'delete': [IsAdministrator],
            'list': [IsAuthenticated],
        },
    }
    
    # Retorna permissões específicas ou padrão
    if resource in permission_map and action in permission_map[resource]:
        return permission_map[resource][action]
    
    # Permissões padrão
    default_permissions = {
        'create': [IsAuthenticated],
        'read': [IsViewer],
        'update': [IsAuthenticated],
        'delete': [IsAdministrator],
        'list': [IsViewer],
    }
    
    return default_permissions.get(action, [IsAuthenticated])