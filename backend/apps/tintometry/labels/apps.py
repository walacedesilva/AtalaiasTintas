"""
Configuração da aplicação de etiquetas
"""
from django.apps import AppConfig


class LabelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tintometry.labels'
    verbose_name = 'Sistema de Etiquetas'
    
    def ready(self):
        """Executado quando a aplicação está pronta"""
        try:
            # Importar sinais se houver
            # from . import signals
            
            # Criar templates padrão se necessário
            from .services import LabelTemplateService
            LabelTemplateService.create_default_templates()
            
        except Exception as e:
            # Log do erro mas não falha a inicialização
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro na inicialização da aplicação labels: {e}")
            pass