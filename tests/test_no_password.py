"""
Archivo: tests/test_no_password.py

Script de pruebas para la gestión de certificados sin contraseña.

Este script valida un caso de uso (edge case) importante: la capacidad de 
la librería para procesar contenedores PKCS#12 (.p12 o .pfx) que han sido 
exportados sin cifrado de clave.

El test automatiza el proceso pasando una cadena vacía ("") como argumento 
de contraseña, verificando que tanto la extracción de información (cryptography) 
como la inyección de la firma (pyHanko) se completan exitosamente sin 
lanzar excepciones de validación.
"""

import os
import sys
import json

# Añadimos el directorio raíz al path para poder importar 'pdfsign'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfsign.certificate import get_certificate_info
from pdfsign.signer import sign_pdf
from pdfsign.pdf import analyze_pdf

def run_test():
    """
    Ejecuta el flujo de prueba automatizado para certificados sin clave.
    
    Flujo de ejecución:
    1. Verifica la existencia del certificado de prueba generado (sin_clave.p12).
    2. Llama a `get_certificate_info` pasando `password=""` para confirmar 
       que el contenedor se puede abrir y leer correctamente.
    3. Llama a `sign_pdf` pasando `password=""` para aplicar la firma en el PDF.
    4. Analiza el documento final para verificar que la firma de "Usuario Sin Clave" 
       está incrustada y mantiene su integridad criptográfica.
    """
    print("=== INICIANDO PRUEBA DE CERTIFICADO SIN CONTRASEÑA ===\n")
    
    cert_path = "certificados/sin_clave.p12"
    input_pdf = "examples/documento_real.pdf"
    output_pdf = "examples/documento_sin_clave.pdf"
    
    if not os.path.exists(cert_path):
        print(f"❌ Error: No se encuentra {cert_path}. Ejecuta los comandos de OpenSSL primero.")
        return

    # 1. Probar extracción de info pasando cadena vacía
    print(f"📄 Analizando certificado: {cert_path}...")
    info_json = get_certificate_info(cert_path, password="")
    info_dict = json.loads(info_json)
    
    if info_dict["status"] == "success":
        print(f"✅ Extracción correcta. Titular: {info_dict['data']['subject_name']}")
    else:
        print(f"❌ Fallo en la extracción: {info_dict['message']}")
        return

    # 2. Probar firma pasando cadena vacía
    print("\n⏳ Firmando documento...")
    firma_json = sign_pdf(input_pdf, cert_path, password="", output_pdf=output_pdf)
    firma_dict = json.loads(firma_json)
    
    if firma_dict["status"] == "success":
        print(f"✅ Documento firmado con éxito en: {output_pdf}")
        
        # 3. Comprobar resultado
        analisis = json.loads(analyze_pdf(output_pdf))
        firmas = analisis["data"].get("signatures", [])
        
        print("\n=== VERIFICACIÓN FINAL ===")
        for f in firmas:
            # Buscamos específicamente la firma que acabamos de realizar
            if "Usuario Sin Clave" in f["signer_name"]:
                print(f"✅ Firma validada en el PDF -> {f['signer_name']} | Íntegro: {f['is_intact']}")
    else:
        print(f"❌ Error al firmar: {firma_dict['message']}")


if __name__ == "__main__":
    run_test()