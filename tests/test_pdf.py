"""
Archivo: tests/test_pdf.py

Script de pruebas para el módulo de análisis y validación de documentos (pdf.py).

Este script verifica la robustez de la librería frente a diferentes escenarios 
de entrada de archivos. Evalúa específicamente la capacidad del sistema para 
detectar archivos inexistentes, archivos corruptos (o falsificados con extensión .pdf) 
y documentos estructuralmente válidos, asegurando que el manejador de excepciones 
devuelve siempre un JSON estructurado y controlado.
"""

import os
import sys

# Añadimos el directorio raíz al path para poder importar 'pdfsign'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfsign.pdf import analyze_pdf


def setup_environment() -> str:
    """
    Prepara el entorno de pruebas creando los directorios y archivos necesarios.
    
    Genera un archivo falso que simula ser un PDF (tiene extensión .pdf pero 
    su contenido es texto plano). Esto permite validar que la librería no se 
    fía solo de la extensión, sino de la estructura binaria del archivo.

    Returns:
        str: La ruta relativa al archivo PDF falso generado.
    """
    os.makedirs("examples", exist_ok=True)
    
    # Creamos un archivo que existe pero NO es un PDF válido
    fake_pdf_path = "examples/falso.pdf"
    with open(fake_pdf_path, "w") as f:
        f.write("Esto es un archivo de texto plano camuflado como PDF.")
        
    return fake_pdf_path


def run_tests():
    """
    Ejecuta la batería de pruebas de validación de archivos PDF.
    
    Flujo de ejecución:
    1. Llama a `setup_environment` para preparar el escenario.
    2. Define tres casos de uso críticos:
       - Un documento PDF válido y real.
       - Un documento falso (texto plano con extensión .pdf).
       - Una ruta hacia un archivo que no existe.
    3. Itera sobre cada caso pasando la ruta a `analyze_pdf`.
    4. Imprime la respuesta JSON generada para auditar el manejo de errores.
    """
    fake_pdf_path = setup_environment()
    real_pdf_path = "examples/documento_real.pdf"
    missing_pdf_path = "examples/no_existe.pdf"

    print("=== INICIANDO PRUEBAS DE PDF ===")
    
    # IMPORTANTE: Debes colocar un PDF real en la carpeta examples con este nombre
    if not os.path.exists(real_pdf_path):
        print(f"\n[AVISO] Por favor, coloca un PDF válido en '{real_pdf_path}' para ver el Caso 1 completo.")

    casos_de_uso = [
        {"nombre": "CASO 1: El documento existe y es un PDF válido", "ruta": real_pdf_path},
        {"nombre": "CASO 2: El documento existe pero NO es PDF", "ruta": fake_pdf_path},
        {"nombre": "CASO 3: El documento NO existe", "ruta": missing_pdf_path}
    ]

    for caso in casos_de_uso:
        print(f"\n{caso['nombre']}")
        print(f"Ruta: {caso['ruta']}")
        print("-" * 40)
        
        # Llamamos a la función que devuelve el JSON
        resultado_json = analyze_pdf(caso["ruta"])
        
        # Imprimimos la respuesta directamente
        print(resultado_json)


if __name__ == "__main__":
    run_tests()