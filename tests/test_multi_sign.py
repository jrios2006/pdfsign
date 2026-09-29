"""
Archivo: tests/test_multi_sign.py

Script de pruebas para la validación de múltiples firmas (firmas incrementales).

Este script verifica uno de los aspectos criptográficos más críticos de la librería:
la capacidad de inyectar una nueva firma en un PDF que ya ha sido firmado 
previamente, sin alterar los bytes originales y, por tanto, sin invalidar 
el hash matemático de la primera firma.

Adicionalmente, implementa y prueba una lógica de negocio común: 
evitar que el mismo usuario (basado en su Common Name) firme el mismo 
documento dos veces.
"""

import os
import sys
import getpass
import json

# Añadimos el directorio raíz al path para poder importar la librería 'pdfsign'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfsign.signer import sign_pdf
from pdfsign.certificate import discover_certificates, get_certificate_info
from pdfsign.pdf import analyze_pdf

def run_tests():
    """
    Ejecuta el flujo de prueba para inyectar una segunda firma en un documento.
    
    Flujo de ejecución:
    1. Lee un documento previamente firmado (ej. generado por test_signer.py) y 
       extrae la lista de firmantes actuales.
    2. Pide al usuario que seleccione un nuevo certificado.
    3. Cruza el Common Name (CN) del certificado seleccionado con la lista de 
       firmantes previos del documento para bloquear firmas duplicadas.
    4. Si el usuario es nuevo, aplica la firma incremental generando un nuevo PDF.
    5. Analiza el documento resultante para confirmar que ambas firmas coexisten 
       y mantienen su integridad (Íntegro: True).
    """
    print("=== INICIANDO PRUEBA DE MÚLTIPLES FIRMAS ===\n")
    
    input_pdf = "examples/documento_firmado.pdf"
    output_pdf = "examples/documento_doble_firma.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"❌ Error: No se encuentra el archivo {input_pdf}. Debes ejecutar test_signer.py primero.")
        return

    # 1. ANALIZAR FIRMANTES EXISTENTES
    print(f"📄 Analizando archivo destino: {os.path.basename(input_pdf)}...")
    analisis_previo = json.loads(analyze_pdf(input_pdf))
    
    if analisis_previo["status"] != "success":
        print(f"❌ Error al leer el PDF: {analisis_previo['message']}")
        return
        
    firmas_previas = analisis_previo["data"]["signatures"]
    firmantes_actuales = [f["signer_name"] for f in firmas_previas]
    
    if firmas_previas:
        print(f"   -> ⚠️ Este documento contiene {len(firmas_previas)} firma(s):")
        for f in firmas_previas:
            print(f"      - {f['signer_name']} (Íntegro: {f['is_intact']})")
    else:
        print("   -> ℹ️ El documento no tiene firmas previas. (Se esperaba que tuviera al menos una).")
    print("-" * 50)

    # 2. SELECCIÓN DE CERTIFICADO
    print("\nBuscando certificados...")
    certificados = discover_certificates()
    for idx, cert in enumerate(certificados):
        print(f"  [{idx + 1}] {os.path.basename(cert)}")
        
    try:
        opcion = int(input(f"\nSelecciona el certificado para la SEGUNDA firma (1-{len(certificados)}): "))
        cert_path = certificados[opcion - 1]
    except (ValueError, IndexError):
        print("❌ Selección inválida. Saliendo.")
        return
        
    password = getpass.getpass(f"Introduce la contraseña para {os.path.basename(cert_path)}: ")

    # 3. COMPROBACIÓN DE FIRMA DUPLICADA
    # Extraemos el nombre (Common Name) del certificado que intenta firmar
    info_cert_json = get_certificate_info(cert_path, password)
    info_cert = json.loads(info_cert_json)
    
    if info_cert["status"] != "success":
        print(f"❌ Error con el certificado: {info_cert['message']}")
        return
        
    nuevo_firmante_cn = info_cert["data"]["subject_name"]
    
    # Comprobamos si el Common Name (CN) del nuevo certificado ya está en la lista de firmantes del PDF
    ya_firmado = any(nuevo_firmante_cn in firmante_existente for firmante_existente in firmantes_actuales)
    
    if ya_firmado:
        print(f"\n🚫 OPERACIÓN CANCELADA: El usuario '{nuevo_firmante_cn}' ya ha firmado este documento.")
        return
    else:
        print(f"\n✅ Verificación superada: '{nuevo_firmante_cn}' no ha firmado aún.")

    # 4. AÑADIR LA SEGUNDA FIRMA
    print("\n⏳ Añadiendo nueva firma...")
    resultado_firma = json.loads(sign_pdf(input_pdf, cert_path, password, output_pdf))
    
    if resultado_firma["status"] == "success":
        print(f"\n✅ ¡Éxito! Documento generado en: {output_pdf}")
        
        # 5. COMPROBAR EL RESULTADO FINAL
        print("\n=== COMPROBANDO EL DOCUMENTO FINAL ===")
        analisis_post = json.loads(analyze_pdf(output_pdf))
        firmas_finales = analisis_post["data"]["signatures"]
        
        print(f"✅ Se han detectado {len(firmas_finales)} firma(s) en total:")
        for idx, f in enumerate(firmas_finales):
            print(f"   [Firma {idx + 1}] {f['signer_name']} | Íntegro: {f['is_intact']}")
    else:
        print(f"❌ Error al firmar: {resultado_firma['message']}")

if __name__ == "__main__":
    run_tests()