"""
Archivo: tests/test_signer.py

Script de pruebas principal para el motor de firma digital (signer.py).

Este script actúa como una prueba de integración (end-to-end) para validar 
el flujo de trabajo completo de un usuario real. Coordina las tres piezas 
principales de la librería:
1. Analiza el PDF origen para comprobar su estado actual.
2. Descubre los certificados y permite al usuario interactuar para elegir uno.
3. Ejecuta la inyección criptográfica de la firma.
4. Vuelve a analizar el PDF resultante para verificar matemáticamente que 
   la firma se ha aplicado correctamente y es íntegra.
"""

import os
import sys
import getpass
import json

# Añadimos el directorio raíz al path para poder importar la librería 'pdfsign'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdfsign.signer import sign_pdf
from pdfsign.certificate import discover_certificates
from pdfsign.pdf import analyze_pdf

def run_tests():
    """
    Ejecuta el flujo interactivo de prueba para firmar un documento PDF.
    
    Flujo de ejecución:
    1. Fase de Análisis: Lee `documento_real.pdf` e imprime su tamaño y estado 
       actual de firmas.
    2. Fase de Selección: Enumera los certificados disponibles y pide al usuario 
       que elija uno introduciendo el número correspondiente, seguido de su contraseña.
    3. Fase de Firma: Llama al motor criptográfico para generar `documento_firmado.pdf`.
    4. Fase de Comprobación: Vuelve a escanear el archivo recién generado para 
       confirmar que el motor pyHanko reconoce la nueva firma incrustada.
    """
    print("=== INICIANDO PRUEBA DE FIRMA DE PDF ===\n")
    
    input_pdf = "examples/documento_real.pdf"
    output_pdf = "examples/documento_firmado.pdf"
    
    # 1. ANÁLISIS PREVIO DEL DOCUMENTO
    print(f"📄 Analizando archivo destino: {os.path.basename(input_pdf)}...")
    analisis_previo = analyze_pdf(input_pdf)
    dict_previo = json.loads(analisis_previo)
    
    if dict_previo["status"] != "success":
        print(f"❌ Error al leer el PDF: {dict_previo['message']}")
        return
        
    peso_kb = dict_previo["data"]["file_info"]["size_bytes"] / 1024
    firmas_previas = dict_previo["data"]["signatures"]
    
    print(f"   -> Tamaño: {peso_kb:.2f} KB")
    if firmas_previas:
        print(f"   -> ⚠️ Este documento ya contiene {len(firmas_previas)} firma(s):")
        for f in firmas_previas:
            print(f"      - {f['signer_name']} (Campo: {f['field_name']})")
    else:
        print("   -> ℹ️ El documento está limpio. No contiene firmas.")
    print("-" * 50)

    # 2. SELECCIÓN DE CERTIFICADO
    print("\nBuscando certificados...")
    certificados = discover_certificates()
    if not certificados:
        print("❌ No se encontraron certificados.")
        return
        
    for idx, cert in enumerate(certificados):
        print(f"  [{idx + 1}] {os.path.basename(cert)} (Ruta: {cert})")
        
    try:
        opcion = int(input(f"\nSelecciona el número de certificado a usar (1-{len(certificados)}): "))
        if opcion < 1 or opcion > len(certificados):
            raise ValueError
        cert_path = certificados[opcion - 1]
    except ValueError:
        print("❌ Selección inválida. Saliendo.")
        return
        
    password = getpass.getpass(f"Introduce la contraseña para {os.path.basename(cert_path)}: ")
    
    # 3. FIRMA DEL DOCUMENTO
    print("\n⏳ Firmando documento...")
    resultado_firma_json = sign_pdf(input_pdf, cert_path, password, output_pdf)
    resultado_firma_dict = json.loads(resultado_firma_json)
    
    if resultado_firma_dict["status"] == "success":
        print(f"\n✅ ¡Éxito! Documento generado en: {output_pdf}")
        print("\n=== COMPROBANDO EL DOCUMENTO FIRMADO ===")
        
        # 4. COMPROBACIÓN POSTERIOR
        analisis_post = analyze_pdf(output_pdf)
        dict_post = json.loads(analisis_post)
        
        if dict_post["status"] == "success":
            firmas = dict_post["data"]["signatures"]
            print(f"\n✅ Se ha detectado {len(firmas)} firma(s) en el documento final:")
            for f in firmas:
                print(f"   -> Firmante: {f['signer_name']} | Íntegro: {f['is_intact']}")
    else:
        print(f"❌ Error al firmar:")
        print(resultado_firma_json)


if __name__ == "__main__":
    run_tests()