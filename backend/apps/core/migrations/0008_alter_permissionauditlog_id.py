import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Synchronize the Python model with the migration state.
    The PermissionAuditLog.id field is explicitly declared in models.py as
    UUIDField(primary_key=True, default=uuid.uuid4, editable=False).
    Migration 0007 already updated the state; this migration makes the state
    fully consistent with the explicit field declaration.
    No database changes are needed — the column is already UUID in PostgreSQL.
    """

    dependencies = [
        ("core", "0007_fix_permissionauditlog_id_uuid"),
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
            database_operations=[],
        )
    ]
