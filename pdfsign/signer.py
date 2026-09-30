"""
Archivo: pdfsign/signer.py

Motor criptográfico y núcleo de firma digital de la librería PdfSign.

Este módulo es el encargado de inyectar las firmas digitales estándar PAdES 
en los documentos PDF. Implementa un diseño robusto basado en dos pilares:

1. Puente criptográfico: Utiliza `cryptography` para abrir de forma segura el 
   contenedor PKCS#12 y luego traduce la clave y el certificado a tipos nativos 
   de `asn1crypto` para que el motor de `pyHanko` pueda procesarlos sin errores.
2. Firma Incremental: Aplica la firma en un archivo en modo lectura/escritura 
   (`rb+`). Esto garantiza que, si el PDF ya tenía firmas previas, no se 
   romperán sus hashes criptográficos originales, logrando una validez 
   perfecta para múltiples firmantes.
"""

import os
import json
import uuid
import shutil
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from asn1crypto import x509, keys as asn1keys

from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
from pyhanko.pdf_utils.reader import PdfFileReader  # <-- Añadido para contar páginas

from .pdf import analyze_pdf
from .visual import calculate_signature_box, create_stamp_style

def sign_pdf(input_pdf: str, cert_path: str, password: str, output_pdf: str, reason: str = "Visado", invisible: bool = False) -> str:
    """
    Firma un documento PDF utilizando un certificado local PKCS#12 (.p12 o .pfx).
    Genera un recuadro visual de firma dinámico para evitar solapamientos.
    
    El archivo original nunca se modifica. Primero se copia a la ruta de destino 
    y luego se abre en modo incremental para inyectar los bytes de la firma y el widget.

    Args:
        input_pdf (str): Ruta al archivo PDF original que se desea firmar.
        cert_path (str): Ruta al archivo del certificado digital (.p12 o .pfx).
        password (str): Contraseña del certificado. (En blanco si no tiene).
        output_pdf (str): Ruta donde se guardará el nuevo PDF firmado.
        reason (str): Motivo de la firma/visado (ej. "Aprobado", "Rechazado").

    Returns:
        str: Cadena JSON indicando el resultado, la ruta y los metadatos.
    """
    if not os.path.exists(input_pdf):
        return json.dumps({"status": "error", "message": f"El PDF original no existe: {input_pdf}", "data": None}, indent=4)
        
    if not os.path.exists(cert_path):
        return json.dumps({"status": "error", "message": f"El certificado no existe: {cert_path}", "data": None}, indent=4)

    # BLOQUE 1: LECTURA DEL CERTIFICADO AISLADA
    password_bytes = password.encode('utf-8') if password else b''
    try:
        with open(cert_path, "rb") as f:
            p12_data = f.read()
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(p12_data, password_bytes)
    except ValueError:
        return json.dumps({"status": "error", "message": "Contraseña incorrecta o certificado inválido.", "data": None}, indent=4)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error crítico al leer certificado: {str(e)}", "data": None}, indent=4)

    # BLOQUE 2: PROCESO DE INYECCIÓN Y FIRMA
    try:
        cert_der_bytes = certificate.public_bytes(serialization.Encoding.DER)
        asn1_cert = x509.Certificate.load(cert_der_bytes)

        key_der_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        asn1_key = asn1keys.PrivateKeyInfo.load(key_der_bytes)

        signer = signers.SimpleSigner(signing_cert=asn1_cert, signing_key=asn1_key, cert_registry=None)
        
        shutil.copy2(input_pdf, output_pdf)
        
        with open(output_pdf, 'rb+') as doc_out:
            writer = IncrementalPdfFileWriter(doc_out)
            nombre_campo = f"Firma_{uuid.uuid4().hex[:6].upper()}"
            
            if not invisible:
                # ==========================================
                # LÓGICA DE FIRMA VISUAL EN ÚLTIMA PÁGINA
                # ==========================================
                # 1. Contar firmas previas para calcular la coordenada vertical
                analisis = json.loads(analyze_pdf(input_pdf))
                num_firmas_previas = len(analisis.get("data", {}).get("signatures", []))
                
                # 2. Leer número de páginas para ubicar el sello en la última
                with open(input_pdf, 'rb') as in_doc:
                    reader = PdfFileReader(in_doc)
                    total_pages = int(reader.root['/Pages']['/Count'])
                    ultima_pagina = total_pages - 1  # pyHanko usa índice base 0
                
                box = calculate_signature_box(num_firmas_previas)
                style = create_stamp_style(reason)

                # 3. Añadir el campo de firma especificando la última página
                append_signature_field(
                    writer, 
                    SigFieldSpec(
                        sig_field_name=nombre_campo, 
                        box=box, 
                        on_page=ultima_pagina
                    )
                )
                
                pdf_signer = signers.PdfSigner(
                    signers.PdfSignatureMetadata(field_name=nombre_campo, reason=reason),
                    signer=signer,
                    stamp_style=style
                )
            else:
                # FIRMA INVISIBLE
                pdf_signer = signers.PdfSigner(
                    signers.PdfSignatureMetadata(field_name=nombre_campo, reason=reason),
                    signer=signer
                )
            
            pdf_signer.sign_pdf(writer, in_place=True)

        cn_attributes = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        signer_name = cn_attributes[0].value if cn_attributes else "Firmante Desconocido"

        return json.dumps({
            "status": "success", 
            "message": "Documento firmado correctamente.", 
            "data": {
                "input_file": os.path.basename(input_pdf),
                "output_file": os.path.basename(output_pdf),
                "signer_name": signer_name,
                "reason": reason,
                "is_invisible": invisible,
                "signature_field": nombre_campo
            }
        }, indent=4, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Fallo en el proceso de firma: {str(e)}", "data": None}, indent=4)