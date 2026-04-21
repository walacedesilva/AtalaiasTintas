from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.core.models import UserGroup, GroupMembership, PermissionAuditLog
import getpass
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria um novo usuário no sistema de tintas'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nome de usuário')
        parser.add_argument('--email', type=str, help='Email do usuário')
        parser.add_argument('--first-name', type=str, help='Primeiro nome')
        parser.add_argument('--last-name', type=str, help='Último nome')
        parser.add_argument('--cpf', type=str, help='CPF do usuário')
        parser.add_argument('--telefone', type=str, help='Telefone do usuário')
        parser.add_argument('--grupo', type=str, help='Grupo do usuário', 
                           choices=['Administradores', 'Gerentes', 'Coloristas', 'Vendedores', 'Estoquistas', 'Visualizador'])
        parser.add_argument('--superuser', action='store_true', help='Criar como superusuário')
        parser.add_argument('--ativo', action='store_true', default=True, help='Usuário ativo (padrão: True)')
        parser.add_argument('--password', type=str, help='Senha do usuário')
        parser.add_argument('--interactive', action='store_true', help='Modo interativo para entrada de dados')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Criador de Usuários - Sistema AtalaiasTintas ===\n'))
        
        # Modo interativo
        if options['interactive']:
            options = self._get_interactive_input(options)
        
        # Validações básicas
        username = options['username']
        
        # Verificar se usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'Usuário "{username}" já existe!')
            )
            return
        
        try:
            with transaction.atomic():
                # Criar usuário
                user_data = self._prepare_user_data(options)
                
                if options['superuser']:
                    user = User.objects.create_superuser(**user_data)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Superusuário "{username}" criado com sucesso!')
                    )
                else:
                    user = User.objects.create_user(**user_data)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Usuário "{username}" criado com sucesso!')
                    )
                
                # Adicionar ao grupo se especificado
                if options['grupo'] and options['grupo'] != 'Visualizador':
                    self._add_to_group(user, options['grupo'])
                
                # Exibir resumo
                self._display_user_summary(user, options['grupo'])
                
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Erro de validação: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar usuário: {e}')
            )

    def _get_interactive_input(self, options):
        """Coleta dados do usuário interativamente"""
        self.stdout.write(self.style.WARNING('Modo interativo ativado. Pressione Enter para pular campos opcionais.\n'))
        
        # Dados obrigatórios
        if not options['username']:
            options['username'] = input('Nome de usuário: ')
        
        # Email
        if not options['email']:
            email = input('Email (opcional): ')
            if email:
                options['email'] = email
        
        # Nome completo
        if not options['first_name']:
            first_name = input('Primeiro nome (opcional): ')
            if first_name:
                options['first_name'] = first_name
                
        if not options['last_name']:
            last_name = input('Último nome (opcional): ')
            if last_name:
                options['last_name'] = last_name
        
        # CPF
        if not options['cpf']:
            cpf = input('CPF (opcional): ')
            if cpf:
                options['cpf'] = cpf
        
        # Telefone
        if not options['telefone']:
            telefone = input('Telefone (opcional): ')
            if telefone:
                options['telefone'] = telefone
        
        # Grupo
        if not options['grupo']:
            self.stdout.write('\nGrupos disponíveis:')
            grupos = ['Visualizador', 'Vendedores', 'Estoquistas', 'Coloristas', 'Gerentes', 'Administradores']
            for i, grupo in enumerate(grupos, 1):
                if grupo == 'Visualizador':
                    self.stdout.write(f'  {i}. {grupo} (apenas visualização - recomendado para ERP)')
                elif grupo == 'Administradores':
                    self.stdout.write(f'  {i}. {grupo} (acesso total - cuidado!)')
                else:
                    self.stdout.write(f'  {i}. {grupo}')
            
            escolha = input(f'Escolha o grupo (1-{len(grupos)}) [1 para Visualizador]: ')
            if escolha and escolha.isdigit() and 1 <= int(escolha) <= len(grupos):
                options['grupo'] = grupos[int(escolha) - 1]
            else:
                options['grupo'] = 'Visualizador'
        
        # Superusuário
        if not options.get('superuser'):
            superuser = input('Criar como superusuário? (s/N): ').lower()
            options['superuser'] = superuser in ['s', 'sim', 'y', 'yes']
        
        # Senha
        if not options['password']:
            while True:
                password = getpass.getpass('Senha: ')
                confirm_password = getpass.getpass('Confirme a senha: ')
                
                if password == confirm_password:
                    if len(password) < 8:
                        self.stdout.write(self.style.ERROR('A senha deve ter pelo menos 8 caracteres.'))
                        continue
                    options['password'] = password
                    break
                else:
                    self.stdout.write(self.style.ERROR('As senhas não coincidem.'))
        
        return options

    def _prepare_user_data(self, options):
        """Prepara os dados do usuário para criação"""
        user_data = {
            'username': options['username'],
            'password': options.get('password', 'temp123456'),  # Senha padrão se não fornecida
            'ativo': options.get('ativo', True),
        }
        
        # Campos opcionais
        optional_fields = ['email', 'first_name', 'last_name', 'cpf', 'telefone']
        for field in optional_fields:
            if options.get(field):
                user_data[field] = options[field]
        
        # Validação de CPF (básica)
        if 'cpf' in user_data:
            cpf = re.sub(r'[^0-9]', '', user_data['cpf'])
            if len(cpf) == 11:
                user_data['cpf'] = cpf
            else:
                raise ValidationError(f'CPF inválido: {options["cpf"]}')
        
        return user_data

    def _add_to_group(self, user, grupo_nome):
        """Adiciona usuário a um grupo específico"""
        try:
            grupo = UserGroup.objects.get(name=grupo_nome)
            membership = user.add_to_group(
                group=grupo,
                is_primary=True,
                added_by=None,  # Sistema
                reason=f'Usuário criado via comando de gerenciamento'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuário adicionado ao grupo "{grupo_nome}"')
            )
            
            # Log da ação
            PermissionAuditLog.log_action(
                action='create_user_and_assign_group',
                actor=user,  # Auto-atribuição na criação
                target_user=user,
                target_group=grupo,
                reason=f'Criação de usuário via comando de gerenciamento'
            )
            
        except UserGroup.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Grupo "{grupo_nome}" não encontrado!')
            )
            raise

    def _display_user_summary(self, user, grupo=None):
        """Exibe resumo do usuário criado"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMO DO USUÁRIO CRIADO'))
        self.stdout.write('='*50)
        
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email or "Não informado"}')
        self.stdout.write(f'Nome: {user.get_full_name() or "Não informado"}')
        self.stdout.write(f'CPF: {user.cpf or "Não informado"}')
        self.stdout.write(f'Telefone: {user.telefone or "Não informado"}')
        self.stdout.write(f'Ativo: {"Sim" if user.ativo else "Não"}')
        self.stdout.write(f'Superusuário: {"Sim" if user.is_superuser else "Não"}')
        
        if grupo:
            self.stdout.write(f'Grupo: {grupo}')
            
            # Mostrar permissões do grupo
            if grupo != 'Visualizador':
                try:
                    group_obj = UserGroup.objects.get(name=grupo)
                    permissions = user._get_group_permissions(group_obj)
                    if permissions:
                        self.stdout.write('\nPermissões principais:')
                        for perm in list(permissions)[:5]:  # Mostrar apenas as 5 primeiras
                            self.stdout.write(f'  - {perm}')
                        if len(permissions) > 5:
                            self.stdout.write(f'  ... e mais {len(permissions) - 5} permissões')
                except:
                    pass
        else:
            self.stdout.write('Grupo: Visualizador (apenas leitura)')
        
        self.stdout.write(f'\nID do usuário: {user.id}')
        self.stdout.write('='*50)
        
        # Avisos importantes
        if grupo == 'Administradores':
            self.stdout.write(
                self.style.ERROR('\n⚠️  ATENÇÃO: Este usuário tem acesso TOTAL ao sistema!')
            )
        elif not grupo or grupo == 'Visualizador':
            self.stdout.write(
                self.style.SUCCESS('\n✓ Usuário criado com perfil de visualização (ideal para ERP)')
            )
        
        self.stdout.write('\n✅ Usuário pronto para usar o sistema!')