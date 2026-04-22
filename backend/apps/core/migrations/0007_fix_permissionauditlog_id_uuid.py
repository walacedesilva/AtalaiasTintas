import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Correção: a tabela core_permissionauditlog foi criada com id UUID (migration 0004).
    A migration 0005 tentou alterar para BigAutoField mas a operação foi removida por
    incompatibilidade com PostgreSQL. Esta migration corrige o estado do Django para
    refletir o que realmente existe no banco (UUID), sem alterar a estrutura do banco.
    """

    dependencies = [
        ("core", "0006_make_audit_actor_optional"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="permissionauditlog",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ],
            database_operations=[],  # coluna já é UUID no banco, sem alteração
        )
    ]
