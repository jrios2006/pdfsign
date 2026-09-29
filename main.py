"""
Interfaz de Línea de Comandos (CLI) para PdfSign.

Este módulo actúa como el punto de entrada principal para interactuar con la 
librería desde la terminal. Utiliza `argparse` para proporcionar subcomandos 
que permiten listar certificados, analizar documentos PDF existentes y firmar 
documentos digitalmente.

Uso general:
    python main.py <comando> [argumentos]

Comandos disponibles:
    - analyze: Analiza un PDF y lista sus propiedades y firmas incrustadas.
    - list-certs: Busca y muestra los certificados disponibles en el sistema.
    - sign: Aplica una firma digital a un documento PDF.
"""

import argparse
import sys
import getpass
import json
import os

# Importamos las funciones desde nuestra librería empaquetada
from pdfsign import analyze_pdf, discover_certificates, sign_pdf


def cmd_analyze(args):
    """
    Ejecuta el subcomando 'analyze'.
    
    Lee un archivo PDF proporcionado por el usuario, extrae su tamaño y 
    las firmas incrustadas, y formatea la salida JSON interna para 
    mostrarla de forma amigable en la terminal.

    Args:
        args (argparse.Namespace): Argumentos parseados de la CLI.
                                   Debe contener `args.pdf_path`.
    """
    print(f"Analizando: {args.pdf_path}\n")
    
    # Llamada a la librería base y parseo de la respuesta JSON
    resultado = json.loads(analyze_pdf(args.pdf_path))
    
    if resultado["status"] == "error":
        print(f"❌ Error: {resultado['message']}")
        sys.exit(1)
        
    data = resultado["data"]
    print(f"Tamaño: {data['file_info']['size_bytes'] / 1024:.2f} KB")
    
    firmas = data["signatures"]
    if not firmas:
        print("ℹ️ El documento no contiene firmas.")
    else:
        print(f"✅ Se encontraron {len(firmas)} firma(s):")
        for i, f in enumerate(firmas, 1):
            print(f"  [{i}] Firmante: {f['signer_name']}")
            print(f"      Íntegro: {f['is_intact']}")


def cmd_list_certs(args):
    """
    Ejecuta el subcomando 'list-certs'.
    
    Llama a la función de descubrimiento de la librería, la cual lee el 
    archivo de configuración (config.json) y escanea los directorios en 
    busca de archivos de certificados válidos (.p12, .pfx).
    
    Args:
        args (argparse.Namespace): Argumentos parseados de la CLI.
    """
    certificados = discover_certificates()
    if not certificados:
        print("❌ No se encontraron certificados en las rutas configuradas.")
        sys.exit(1)
        
    print(f"✅ Se encontraron {len(certificados)} certificado(s):")
    for i, cert in enumerate(certificados, 1):
        print(f"  [{i}] {cert}")


def cmd_sign(args):
    """
    Ejecuta el subcomando 'sign'.
    
    Orquesta el flujo completo de firma digital:
    1. Valida la existencia de los archivos de entrada y certificado.
    2. Comprueba si el documento ya tiene firmas para avisar al usuario.
    3. Solicita la contraseña del contenedor criptográfico de forma segura.
    4. Ejecuta la firma y genera el nuevo archivo de salida.

    Args:
        args (argparse.Namespace): Argumentos parseados de la CLI.
                                   Debe contener `args.input_pdf`, 
                                   `args.cert_path` y `args.output_pdf`.
    """
    # Validaciones previas de rutas
    if not os.path.exists(args.input_pdf):
        print(f"❌ Error: El archivo de entrada '{args.input_pdf}' no existe.")
        sys.exit(1)
        
    if not os.path.exists(args.cert_path):
        print(f"❌ Error: El certificado '{args.cert_path}' no existe.")
        sys.exit(1)

    # Comprobación de firma duplicada (opcional pero recomendada)
    analisis_previo = json.loads(analyze_pdf(args.input_pdf))
    if analisis_previo["status"] == "success" and analisis_previo["data"]["signatures"]:
        print("⚠️ Nota: El documento ya contiene firmas previas. Se añadirá una nueva.")

    # Petición segura de contraseña (se oculta en la terminal)
    password = getpass.getpass(f"Introduce la contraseña para el certificado: ")
    print("⏳ Firmando documento...")
    
    # Inyección criptográfica y procesado del resultado
    resultado = json.loads(sign_pdf(args.input_pdf, args.cert_path, password, args.output_pdf))
    
    if resultado["status"] == "success":
        print(f"✅ ¡Éxito! Documento firmado y guardado en: {args.output_pdf}")
    else:
        print(f"❌ Error al firmar: {resultado['message']}")
        sys.exit(1)


def main():
    """
    Punto de entrada principal del script.
    
    Configura el analizador de argumentos de línea de comandos (argparse),
    define la estructura de los subcomandos disponibles y delega la ejecución
    a la función controladora correspondiente.
    """
    parser = argparse.ArgumentParser(
        description="PdfSign - Herramienta profesional para firma digital de PDFs",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(title="Comandos", dest="command", required=True)

    # Subcomando: analyze
    parser_analyze = subparsers.add_parser("analyze", help="Analiza un PDF y muestra sus firmas")
    parser_analyze.add_argument("pdf_path", help="Ruta al archivo PDF que deseas analizar")

    # Subcomando: list-certs
    parser_certs = subparsers.add_parser("list-certs", help="Lista los certificados disponibles según config.json")

    # Subcomando: sign
    parser_sign = subparsers.add_parser("sign", help="Firma un documento PDF con un certificado")
    parser_sign.add_argument("input_pdf", help="Ruta al PDF original")
    parser_sign.add_argument("cert_path", help="Ruta al certificado (.p12 o .pfx)")
    parser_sign.add_argument("output_pdf", help="Ruta donde se guardará el nuevo PDF firmado")

    # Parsear y despachar
    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "list-certs":
        cmd_list_certs(args)
    elif args.command == "sign":
        cmd_sign(args)


if __name__ == "__main__":
    main()