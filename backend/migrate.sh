#!/bin/bash
echo "=== INICIANDO SCRIPT DE MIGRACIÓN ==="
echo "Aplicando migraciones de Django..."
python manage.py migrate

echo "=== CREANDO Y APLICANDO MIGRACIÓN PARA CAMPO VARIANT_ID ==="
python manage.py makemigrations facturacion --name add_variant_id_to_producto
python manage.py migrate facturacion

echo "=== EJECUTANDO COMANDO PARA ACTUALIZAR VARIANT_IDS ==="
python manage.py actualizar_variant_ids

echo "=== MIGRACIÓN COMPLETADA ===" 