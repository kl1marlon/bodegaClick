# Generated by Django 4.2 on 2025-03-19 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detallefactura',
            name='porcentaje_ganancia',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='porcentaje_ganancia',
            field=models.DecimalField(decimal_places=2, default=30.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='producto',
            name='precio_compra',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='producto',
            name='precio_venta_calculado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='producto',
            name='ultima_actualizacion_precio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='producto',
            name='unidades_compra',
            field=models.IntegerField(default=1),
        ),
    ]
