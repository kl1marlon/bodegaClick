# Generated manually for adding user field to TasaCambio model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('facturacion', '0014_merge_20250427_2058'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasacambio',
            name='user',
            field=models.ForeignKey(
                default=1,  # Asignar al primer usuario (generalmente admin)
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuario que creó/modificó la tasa',
            ),
            preserve_default=False,  # Eliminar el default después de la migración
        ),
    ]
