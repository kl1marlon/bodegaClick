#!/usr/bin/env python3
"""
Script para encontrar archivos con bytes nulos en el proyecto.
Los archivos con bytes nulos causan el error:
'ValueError: source code string cannot contain null bytes'
"""

import os
import sys

def check_file_for_null_bytes(file_path):
    """Verifica si un archivo contiene bytes nulos."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if b'\x00' in content:
                return True
    except Exception as e:
        print(f"Error al leer {file_path}: {e}")
    return False

def find_all_python_files(directory):
    """Busca todos los archivos Python en un directorio de forma recursiva."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.pyc'):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    return python_files

def main():
    """Función principal que busca bytes nulos en archivos Python."""
    # Usar el directorio actual o el directorio proporcionado como argumento
    directory = os.getcwd() if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"Buscando archivos Python con bytes nulos en: {directory}")
    
    python_files = find_all_python_files(directory)
    
    print(f"Encontrados {len(python_files)} archivos Python para examinar.")
    
    files_with_null_bytes = []
    
    for file_path in python_files:
        if check_file_for_null_bytes(file_path):
            files_with_null_bytes.append(file_path)
            print(f"⚠️ ARCHIVO CON BYTES NULOS: {file_path}")
    
    if files_with_null_bytes:
        print("\nResumen:")
        print(f"Se encontraron {len(files_with_null_bytes)} archivos con bytes nulos:")
        for file_path in files_with_null_bytes:
            print(f"- {file_path}")
        print("\nEstos archivos pueden causar el error 'ValueError: source code string cannot contain null bytes'")
        print("Recomendación: Elimina o reescribe estos archivos.")
    else:
        print("\nNo se encontraron archivos con bytes nulos.")

if __name__ == "__main__":
    main() 