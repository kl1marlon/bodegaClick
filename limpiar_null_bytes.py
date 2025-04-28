import os

# Cambia esta ruta a la raíz de tu proyecto si lo necesitas
directorio_raiz = os.path.dirname(os.path.abspath(__file__))

archivos_corregidos = []
archivos_afectados = []

for root, dirs, files in os.walk(directorio_raiz):
    for file in files:
        if file.endswith('.py'):
            ruta = os.path.join(root, file)
            with open(ruta, 'rb') as f:
                contenido = f.read()
            if b'\x00' in contenido:
                archivos_afectados.append(ruta)
                contenido_limpio = contenido.replace(b'\x00', b'')
                # Haz backup del archivo original
                os.rename(ruta, ruta + '.bak_nullbyte')
                # Guarda el archivo limpio
                with open(ruta, 'wb') as f:
                    f.write(contenido_limpio)
                archivos_corregidos.append(ruta)

print('Archivos .py con null bytes encontrados y corregidos:')
for a in archivos_corregidos:
    print(' -', a)

if not archivos_corregidos:
    print('No se encontraron archivos .py con null bytes.')
else:
    print('\nSe crearon backups con sufijo .bak_nullbyte por seguridad.')
