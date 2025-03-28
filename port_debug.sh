#!/bin/bash

# Script de diagnóstico específico para problemas de puerto en Railway
echo "===== DIAGNÓSTICO DE PUERTO RAILWAY ====="
echo "Fecha: $(date)"

# Verificar existencia y valores de variable PORT
echo -e "\n== VARIABLE DE ENTORNO PORT =="
if [ -z "${PORT}" ]; then
  echo "Variable PORT no está definida en el entorno"
else
  echo "Valor de PORT: ${PORT}"
fi

# Verificar cómo Railway podría estar configurando el puerto
echo -e "\n== VARIABLES RAILWAY RELACIONADAS CON PUERTOS =="
env | grep -i "PORT\|RAILWAY\|BIND" || echo "No se encontraron variables relacionadas"

# Verificar puertos escuchando
echo -e "\n== PUERTOS ESCUCHANDO =="
netstat -tulpn 2>/dev/null || ss -tulpn 2>/dev/null || echo "No se pudo obtener información de puertos"

# Verificar configuración en archivos
echo -e "\n== CONFIGURACIÓN DE PUERTO EN ARCHIVOS =="
echo "Dockerfile:"
grep -n "PORT\|EXPOSE" Dockerfile || echo "No se encontró configuración de puerto"

echo -e "\nProcfile:"
if [ -f "Procfile" ]; then
  grep -n "bind\|port" Procfile || echo "No se encontró configuración de puerto"
else
  echo "No existe archivo Procfile"
fi

echo -e "\nrailway.json/toml:"
if [ -f "railway.json" ]; then
  grep -n "bind\|port" railway.json || echo "No se encontró configuración de puerto"
elif [ -f "railway.toml" ]; then
  grep -n "bind\|port" railway.toml || echo "No se encontró configuración de puerto"
else
  echo "No existe archivo railway.json o railway.toml"
fi

# Verificar permisos de puertos
echo -e "\n== PERMISOS DE PUERTOS =="
if [ "$(id -u)" -eq 0 ]; then
  echo "Ejecutando como root - no hay restricciones de puertos por permisos"
else
  echo "Ejecutando como usuario no-root - puertos < 1024 requieren privilegios especiales"
  if [[ "${PORT}" -lt 1024 ]]; then
    echo "ADVERTENCIA: Puerto ${PORT} es menor que 1024, puede requerir privilegios root"
  fi
fi

# Probar conexión a puertos comunes de Railway
echo -e "\n== PRUEBA DE CONEXIÓN A PUERTOS COMUNES =="
for test_port in 3000 8000 8080; do
  nc -z -v localhost $test_port 2>&1 || echo "Puerto $test_port no está en uso"
done

echo -e "\n===== FIN DEL DIAGNÓSTICO DE PUERTO =====" 