#!/bin/bash

# Script para diagnóstico previo al despliegue en Railway
# Guardar en logs/deploy_diagnosis.log

# Crear directorio de logs si no existe
mkdir -p logs
LOG_FILE="logs/deploy_diagnosis.log"

echo "===== DIAGNÓSTICO DE DESPLIEGUE =====" > $LOG_FILE
echo "Fecha y hora: $(date)" >> $LOG_FILE
echo "" >> $LOG_FILE

echo "===== INFORMACIÓN DEL SISTEMA =====" >> $LOG_FILE
echo "Sistema operativo: $(uname -a)" >> $LOG_FILE
echo "Python: $(python --version 2>&1)" >> $LOG_FILE
echo "Pip: $(pip --version 2>&1)" >> $LOG_FILE
echo "" >> $LOG_FILE

echo "===== ESTRUCTURA DEL PROYECTO =====" >> $LOG_FILE
echo "Directorio actual: $(pwd)" >> $LOG_FILE
echo "Contenido del directorio raíz:" >> $LOG_FILE
ls -la >> $LOG_FILE
echo "" >> $LOG_FILE

echo "===== VERIFICACIÓN DE ARCHIVOS CRÍTICOS =====" >> $LOG_FILE
for file in Dockerfile railway.json Procfile backend/wsgi.py backend/settings.py
do
  if [ -f "$file" ]; then
    echo "✅ $file existe" >> $LOG_FILE
  else
    echo "❌ $file NO EXISTE" >> $LOG_FILE
  fi
done
echo "" >> $LOG_FILE

echo "===== CONTENIDO DE ARCHIVOS DE CONFIGURACIÓN =====" >> $LOG_FILE
echo "== Dockerfile ==" >> $LOG_FILE
cat Dockerfile >> $LOG_FILE
echo "" >> $LOG_FILE

echo "== railway.json ==" >> $LOG_FILE
cat railway.json >> $LOG_FILE
echo "" >> $LOG_FILE

echo "== Procfile ==" >> $LOG_FILE
if [ -f "Procfile" ]; then
  cat Procfile >> $LOG_FILE
else
  echo "No existe Procfile" >> $LOG_FILE
fi
echo "" >> $LOG_FILE

echo "== .env.railway (sin valores sensibles) ==" >> $LOG_FILE
if [ -f ".env.railway" ]; then
  grep -v "PASSWORD\|SECRET\|TOKEN" .env.railway | sed 's/=.*/=***/' >> $LOG_FILE
else
  echo "No existe .env.railway" >> $LOG_FILE
fi
echo "" >> $LOG_FILE

echo "===== VERIFICACIÓN DE CONFIGURACIÓN DE PUERTO =====" >> $LOG_FILE
echo "Puerto configurado en Dockerfile:" >> $LOG_FILE
grep -n "EXPOSE\|PORT" Dockerfile >> $LOG_FILE
echo "" >> $LOG_FILE

echo "Puerto configurado en railway.json:" >> $LOG_FILE
grep -n "bind\|port" railway.json >> $LOG_FILE
echo "" >> $LOG_FILE

if [ -f "Procfile" ]; then
  echo "Puerto configurado en Procfile:" >> $LOG_FILE
  grep -n "bind\|port" Procfile >> $LOG_FILE
  echo "" >> $LOG_FILE
fi

echo "===== VERIFICANDO ACCESO A RAILWAY =====" >> $LOG_FILE
railway whoami >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

railway status >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

echo "===== FIN DEL DIAGNÓSTICO =====" >> $LOG_FILE
echo "Log guardado en $LOG_FILE"

# Mostrar resumen en pantalla
cat $LOG_FILE 