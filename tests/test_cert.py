"""
Archivo: tests/test_cert.py

Script de pruebas para el módulo de gestión de certificados (certificate.py).

Este script actúa como una herramienta de validación independiente para 
comprobar que la librería es capaz de:
1. Leer el archivo `config.json` y localizar correctamente los archivos 
   .p12 o .pfx en los directorios especificados.
2. Manejar de forma segura la entrada de contraseñas por terminal.
3. Desencriptar el contenedor criptográfico y extraer los metadatos públicos 
   sin exponer la clave privada, evaluando la respuesta JSON estructurada.
"""

import os
import sys
import getpass
import json

# Añadimos el directorio raíz al path para poder importar 'pdfsign'
# Esto permite ejecutar el test desde cualquier subcarpeta sin romper los imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfsign.certificate import discover_certificates, get_certificate_info

def run_tests():
    """
    Ejecuta el flujo completo de prueba de certificados.
    
    Flujo de ejecución:
    1. Llama a `discover_certificates()` para listar todos los certificados disponibles.
    2. Itera sobre cada certificado encontrado.
    3. Solicita la contraseña al usuario de forma segura (oculta) mediante `getpass`.
    4. Llama a `get_certificate_info()` para intentar extraer los datos.
    5. Parsea la respuesta JSON y muestra un resumen amigable en la consola, 
       seguido de la respuesta cruda para auditoría.
    """
    print("=== INICIANDO PRUEBAS DE DESCUBRIMIENTO DE CERTIFICADOS ===")
    
    # 1. Probar descubrimiento
    print("\nBuscando certificados según config.json...")
    certificados_encontrados = discover_certificates()
    
    if not certificados_encontrados:
        print("❌ No se encontraron certificados en las rutas definidas.")
        print("Asegúrate de tener un archivo .p12 o .pfx en las rutas configuradas.")
        return

    print(f"✅ Se han encontrado {len(certificados_encontrados)} certificados:")
    for idx, cert_path in enumerate(certificados_encontrados):
        print(f"  [{idx + 1}] {cert_path}")
        
    print("\n=== PRUEBA DE EXTRACCIÓN Y CONTRASEÑAS ===")
    
    # 2. Iterar sobre los certificados encontrados y probar contraseña
    for cert_path in certificados_encontrados:
        print("-" * 50)
        print(f"Evaluando: {os.path.basename(cert_path)}")
        
        # getpass pide la contraseña por terminal ocultando los caracteres.
        # Si el certificado no tiene contraseña, el usuario solo debe presionar Enter.
        password = getpass.getpass("Introduce la contraseña (o presiona Enter para intentar en blanco): ")
        
        # Llamada a la función principal del módulo certificate
        resultado_json = get_certificate_info(cert_path, password)
        
        # Parseamos el JSON para evaluar si la prueba fue un éxito o un error
        resultado_dict = json.loads(resultado_json)
        
        if resultado_dict["status"] == "success":
            print("\n✅ Contraseña CORRECTA. Datos extraídos:")
            print(f"   -> Titular: {resultado_dict['data']['subject_name']}")
            print(f"   -> Validez: Hasta {resultado_dict['data']['valid_until']}")
        else:
            print("\n❌ Error al abrir el certificado:")
            print(f"   -> Mensaje: {resultado_dict['message']}")
            
        print("\n[Respuesta JSON devuelta por la función]")
        print(resultado_json)


if __name__ == "__main__":
    # Nos aseguramos de estar ejecutando desde un directorio que tenga la carpeta config/
    if not os.path.exists("config/config.json"):
        print("⚠️ Advertencia: No se encuentra config/config.json. Se usarán rutas por defecto.")
        
    run_tests()