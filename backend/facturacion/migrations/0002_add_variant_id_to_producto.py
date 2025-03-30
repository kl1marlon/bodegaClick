from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='variant_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ] 