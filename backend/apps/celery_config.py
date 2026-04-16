"""
Override do AppConfig do django_celery_beat para exibir nome em Português no admin.
"""
from django_celery_beat.apps import BeatConfig


class BeatConfigPtBr(BeatConfig):
    name = 'django_celery_beat'
    verbose_name = 'Tarefas Periódicas'

    def ready(self):
        super().ready()
        _traduzir_admin_celery_beat()


def _traduzir_admin_celery_beat():
    from django.contrib import admin
    from django_celery_beat.models import (
        ClockedSchedule,
        CrontabSchedule,
        IntervalSchedule,
        PeriodicTask,
        SolarSchedule,
    )
    from django_celery_beat.admin import (
        ClockedScheduleAdmin,
        CrontabScheduleAdmin,
        IntervalScheduleAdmin,
        PeriodicTaskAdmin,
        SolarScheduleAdmin,
    )

    _TRADUCOES = {
        ClockedSchedule: ('Agendamento Pontual', 'Agendamentos Pontuais', ClockedScheduleAdmin),
        CrontabSchedule: ('Crontab', 'Crontabs', CrontabScheduleAdmin),
        IntervalSchedule: ('Intervalo', 'Intervalos', IntervalScheduleAdmin),
        PeriodicTask: ('Tarefa Periódica', 'Tarefas Periódicas', PeriodicTaskAdmin),
        SolarSchedule: ('Evento Solar', 'Eventos Solares', SolarScheduleAdmin),
    }

    for model, (singular, plural, admin_class) in _TRADUCOES.items():
        try:
            admin.site.unregister(model)
        except admin.sites.NotRegistered:
            pass

        model._meta.verbose_name = singular
        model._meta.verbose_name_plural = plural
        admin.site.register(model, admin_class)
