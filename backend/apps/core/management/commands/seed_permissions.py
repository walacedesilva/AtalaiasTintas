from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Permission, UserGroup, User


class Command(BaseCommand):
    help = 'Seed initial permissions for the hierarchical permission system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing permissions and groups'
        )

    def handle(self, *args, **options):
        overwrite = options.get('overwrite', False)
        
        self.stdout.write(self.style.SUCCESS('Seeding hierarchical permission system...'))
        
        with transaction.atomic():
            # Create basic permissions for tintometry system
            permissions_data = [
                # Tintometry Module
                {
                    'module': 'tintometry',
                    'resource': 'formula',
                    'action': 'view',
                    'name': 'Visualizar Fórmulas',
                    'description': 'Permite visualizar fórmulas tintométricas'
                },
                {
                    'module': 'tintometry',
                    'resource': 'formula',
                    'action': 'create',
                    'name': 'Criar Fórmulas',
                    'description': 'Permite criar novas fórmulas tintométricas'
                },
                {
                    'module': 'tintometry',
                    'resource': 'formula',
                    'action': 'edit',
                    'name': 'Editar Fórmulas',
                    'description': 'Permite editar fórmulas tintométricas existentes'
                },
                {
                    'module': 'tintometry',
                    'resource': 'formula',
                    'action': 'delete',
                    'name': 'Excluir Fórmulas',
                    'description': 'Permite excluir fórmulas tintométricas'
                },
                {
                    'module': 'tintometry',
                    'resource': 'batch',
                    'action': 'mix',
                    'name': 'Misturar Lote',
                    'description': 'Permite executar mistura de tintas'
                },
                {
                    'module': 'tintometry',
                    'resource': 'batch',
                    'action': 'adjust',
                    'name': 'Ajustar Mistura',
                    'description': 'Permite ajustar proporções da mistura'
                },
                
                # Sales Module
                {
                    'module': 'sales',
                    'resource': 'order',
                    'action': 'view',
                    'name': 'Visualizar Pedidos',
                    'description': 'Permite visualizar pedidos de venda'
                },
                {
                    'module': 'sales',
                    'resource': 'order',
                    'action': 'create',
                    'name': 'Criar Pedidos',
                    'description': 'Permite criar novos pedidos de venda'
                },
                {
                    'module': 'sales',
                    'resource': 'order',
                    'action': 'cancel',
                    'name': 'Cancelar Pedidos',
                    'description': 'Permite cancelar pedidos de venda'
                },
                {
                    'module': 'sales',
                    'resource': 'discount',
                    'action': 'apply',
                    'name': 'Aplicar Descontos',
                    'description': 'Permite aplicar descontos em vendas'
                },
                
                # Inventory Module
                {
                    'module': 'inventory',
                    'resource': 'product',
                    'action': 'view',
                    'name': 'Visualizar Produtos',
                    'description': 'Permite visualizar produtos do estoque'
                },
                {
                    'module': 'inventory',
                    'resource': 'product',
                    'action': 'edit',
                    'name': 'Editar Produtos',
                    'description': 'Permite editar informações de produtos'
                },
                {
                    'module': 'inventory',
                    'resource': 'stock',
                    'action': 'adjust',
                    'name': 'Ajustar Estoque',
                    'description': 'Permite fazer ajustes manuais de estoque'
                },
                {
                    'module': 'inventory',
                    'resource': 'report',
                    'action': 'generate',
                    'name': 'Gerar Relatórios',
                    'description': 'Permite gerar relatórios de estoque'
                },
                
                # Financial Module
                {
                    'module': 'financial',
                    'resource': 'report',
                    'action': 'view',
                    'name': 'Visualizar Relatórios Financeiros',
                    'description': 'Permite visualizar relatórios financeiros'
                },
                {
                    'module': 'financial',
                    'resource': 'payment',
                    'action': 'process',
                    'name': 'Processar Pagamentos',
                    'description': 'Permite processar pagamentos de clientes'
                },
                
                # System Administration
                {
                    'module': 'admin',
                    'resource': 'user',
                    'action': 'manage',
                    'name': 'Gerenciar Usuários',
                    'description': 'Permite gerenciar usuários do sistema'
                },
                {
                    'module': 'admin',
                    'resource': 'permission',
                    'action': 'manage',
                    'name': 'Gerenciar Permissões',
                    'description': 'Permite gerenciar permissões do sistema'
                },
                {
                    'module': 'admin',
                    'resource': 'system',
                    'action': 'configure',
                    'name': 'Configurar Sistema',
                    'description': 'Permite configurar parâmetros do sistema'
                },
            ]
            
            # Create or update permissions
            created_permissions = 0
            updated_permissions = 0
            
            for perm_data in permissions_data:
                permission, created = Permission.objects.get_or_create(
                    module=perm_data['module'],
                    resource=perm_data['resource'],
                    action=perm_data['action'],
                    defaults={
                        'name': perm_data['name'],
                        'description': perm_data['description'],
                        'is_active': True,
                        'is_system': True
                    }
                )
                
                if created:
                    created_permissions += 1
                    self.stdout.write(f'  ✓ Criada: {permission.code}')
                elif overwrite:
                    permission.name = perm_data['name']
                    permission.description = perm_data['description']
                    permission.save()
                    updated_permissions += 1
                    self.stdout.write(f'  ↻ Atualizada: {permission.code}')
                else:
                    self.stdout.write(f'  - Existente: {permission.code}')
            
            # Create default groups
            groups_data = [
                {
                    'name': 'Administradores',
                    'description': 'Administradores do sistema com acesso total',
                    'is_system': True
                },
                {
                    'name': 'Gerentes',
                    'description': 'Gerentes com acesso a relatórios e supervisão',
                    'is_system': True
                },
                {
                    'name': 'Coloristas',
                    'description': 'Especialistas em tintometria e mistura de cores',
                    'is_system': True
                },
                {
                    'name': 'Vendedores',
                    'description': 'Equipe de vendas com acesso ao PDV',
                    'is_system': True
                },
                {
                    'name': 'Estoquistas',
                    'description': 'Responsáveis pelo controle de estoque',
                    'is_system': True
                },
            ]
            
            created_groups = 0
            updated_groups = 0
            
            for group_data in groups_data:
                group, created = UserGroup.objects.get_or_create(
                    name=group_data['name'],
                    defaults={
                        'description': group_data['description'],
                        'is_active': True,
                        'is_system': group_data['is_system']
                    }
                )
                
                if created:
                    created_groups += 1
                    self.stdout.write(f'  ✓ Criado grupo: {group.name}')
                elif overwrite:
                    group.description = group_data['description']
                    group.save()
                    updated_groups += 1
                    self.stdout.write(f'  ↻ Atualizado grupo: {group.name}')
                else:
                    self.stdout.write(f'  - Grupo existente: {group.name}')
            
            # Apply default permissions to groups
            self._assign_group_permissions()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\\nSeeding concluído!\\n'
                    f'  Permissões criadas: {created_permissions}\\n'
                    f'  Permissões atualizadas: {updated_permissions}\\n'
                    f'  Grupos criados: {created_groups}\\n'
                    f'  Grupos atualizados: {updated_groups}\\n'
                )
            )
    
    def _assign_group_permissions(self):
        """Atribui permissões padrão aos grupos"""
        from apps.core.models import GroupPermission
        
        # Get groups
        admin_group = UserGroup.objects.get(name='Administradores')
        manager_group = UserGroup.objects.get(name='Gerentes')  
        colorist_group = UserGroup.objects.get(name='Coloristas')
        sales_group = UserGroup.objects.get(name='Vendedores')
        stock_group = UserGroup.objects.get(name='Estoquistas')
        
        # Administrators - Full access
        admin_permissions = Permission.objects.all()
        for perm in admin_permissions:
            GroupPermission.objects.get_or_create(
                group=admin_group,
                permission=perm,
                defaults={
                    'grant_type': 'allow',
                    'is_active': True,
                    'inherit_to_children': True,
                    'reason': 'Permissões de administrador'
                }
            )
        
        # Managers - Reports and supervision
        manager_permission_codes = [
            'tintometry.formula.view',
            'sales.order.view',
            'inventory.product.view',
            'inventory.report.generate',
            'financial.report.view'
        ]
        for code in manager_permission_codes:
            try:
                perm = Permission.objects.get(
                    module=code.split('.')[0],
                    resource=code.split('.')[1], 
                    action=code.split('.')[2]
                )
                GroupPermission.objects.get_or_create(
                    group=manager_group,
                    permission=perm,
                    defaults={
                        'grant_type': 'allow',
                        'is_active': True,
                        'reason': 'Permissões de gerência'
                    }
                )
            except Permission.DoesNotExist:
                pass
        
        # Colorists - Tintometry focused
        colorist_permission_codes = [
            'tintometry.formula.view',
            'tintometry.formula.create',
            'tintometry.formula.edit',
            'tintometry.batch.mix',
            'tintometry.batch.adjust'
        ]
        for code in colorist_permission_codes:
            try:
                perm = Permission.objects.get(
                    module=code.split('.')[0],
                    resource=code.split('.')[1],
                    action=code.split('.')[2]
                )
                GroupPermission.objects.get_or_create(
                    group=colorist_group,
                    permission=perm,
                    defaults={
                        'grant_type': 'allow',
                        'is_active': True,
                        'reason': 'Permissões de colorista'
                    }
                )
            except Permission.DoesNotExist:
                pass
        
        # Sales team - Sales operations
        sales_permission_codes = [
            'sales.order.view',
            'sales.order.create',
            'sales.discount.apply',
            'inventory.product.view'
        ]
        for code in sales_permission_codes:
            try:
                perm = Permission.objects.get(
                    module=code.split('.')[0],
                    resource=code.split('.')[1],
                    action=code.split('.')[2]
                )
                GroupPermission.objects.get_or_create(
                    group=sales_group,
                    permission=perm,
                    defaults={
                        'grant_type': 'allow',
                        'is_active': True,
                        'reason': 'Permissões de vendas'
                    }
                )
            except Permission.DoesNotExist:
                pass
        
        # Stock team - Inventory management
        stock_permission_codes = [
            'inventory.product.view',
            'inventory.product.edit',
            'inventory.stock.adjust',
            'inventory.report.generate'
        ]
        for code in stock_permission_codes:
            try:
                perm = Permission.objects.get(
                    module=code.split('.')[0],
                    resource=code.split('.')[1],
                    action=code.split('.')[2]
                )
                GroupPermission.objects.get_or_create(
                    group=stock_group,
                    permission=perm,
                    defaults={
                        'grant_type': 'allow',
                        'is_active': True,
                        'reason': 'Permissões de estoque'
                    }
                )
            except Permission.DoesNotExist:
                pass
        
        self.stdout.write('  ✓ Permissões atribuídas aos grupos')