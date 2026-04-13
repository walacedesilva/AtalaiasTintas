"""
Override do AppConfig do django_celery_beat para exibir nome em Português no admin.
"""
from django_celery_beat.apps import BeatConfig


class BeatConfigPtBr(BeatConfig):
    name = 'django_celery_beat'
    verbose_name = 'Tarefas Periódicas'
