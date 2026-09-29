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

def sign_pdf(input_pdf: str, cert_path: str, password: str, output_pdf: str) -> str:
    """
    Firma un documento PDF utilizando un certificado local PKCS#12 (.p12 o .pfx).
    
    El archivo original nunca se modifica. Primero se copia a la ruta de destino 
    y luego se abre en modo incremental para inyectar los bytes de la firma. 
    Esto permite añadir firmas a documentos que ya han sido firmados por otros 
    usuarios sin invalidar el documento.

    Args:
        input_pdf (str): Ruta al archivo PDF original que se desea firmar.
        cert_path (str): Ruta al archivo del certificado digital (.p12 o .pfx).
        password (str): Contraseña del certificado. Si el certificado no tiene 
                        contraseña, se debe pasar un string vacío ("").
        output_pdf (str): Ruta donde se guardará el nuevo PDF firmado.

    Returns:
        str: Cadena en formato JSON indicando el resultado de la operación:
             - status: "success" o "error"
             - message: Mensaje descriptivo
             - data: Diccionario con detalles del archivo origen, destino, 
                     nombre del firmante y el identificador del campo de firma.
    """
    if not os.path.exists(input_pdf):
        return json.dumps({
            "status": "error", 
            "message": f"El PDF original no existe: {input_pdf}", 
            "data": None
        }, indent=4)
        
    if not os.path.exists(cert_path):
        return json.dumps({
            "status": "error", 
            "message": f"El certificado no existe: {cert_path}", 
            "data": None
        }, indent=4)

    try:
        # 1. Leer el certificado y la clave con cryptography de forma segura
        password_bytes = password.encode('utf-8') if password else b''
        
        with open(cert_path, "rb") as f:
            p12_data = f.read()

        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            p12_data, 
            password_bytes
        )

        # 2. CONVERTIR EL CERTIFICADO al formato asn1crypto
        cert_der_bytes = certificate.public_bytes(serialization.Encoding.DER)
        asn1_cert = x509.Certificate.load(cert_der_bytes)

        # 3. CONVERTIR LA CLAVE PRIVADA al formato asn1crypto
        key_der_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        asn1_key = asn1keys.PrivateKeyInfo.load(key_der_bytes)

        # 4. Inyectar los objetos ya convertidos en el motor de pyHanko
        signer = signers.SimpleSigner(
            signing_cert=asn1_cert,
            signing_key=asn1_key,
            cert_registry=None
        )
        
        # 5. Copiar el archivo original para trabajar con seguridad física
        shutil.copy2(input_pdf, output_pdf)
        
        # 6. Abrir y firmar en modo lectura/escritura incremental (in_place=True)
        with open(output_pdf, 'rb+') as doc_out:
            writer = IncrementalPdfFileWriter(doc_out)
            
            # Generamos un identificador único para que múltiples firmas no colisionen
            nombre_campo = f"Firma_{uuid.uuid4().hex[:6].upper()}"
            
            pdf_signer = signers.PdfSigner(
                signers.PdfSignatureMetadata(field_name=nombre_campo),
                signer=signer
            )
            
            # Ejecutar firma física
            pdf_signer.sign_pdf(writer, in_place=True)

        # 7. EXTRAER EL NOMBRE DEL FIRMANTE CORRECTAMENTE (Con cryptography)
        cn_attributes = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        signer_name = cn_attributes[0].value if cn_attributes else "Firmante Desconocido"

        return json.dumps({
            "status": "success", 
            "message": "Documento firmado correctamente.", 
            "data": {
                "input_file": os.path.basename(input_pdf),
                "output_file": os.path.basename(output_pdf),
                "signer_name": signer_name,
                "signature_field": nombre_campo
            }
        }, indent=4, ensure_ascii=False)

    except ValueError:
        # Lanzado típicamente por load_key_and_certificates al fallar el password
        return json.dumps({
            "status": "error", 
            "message": "Contraseña incorrecta o certificado inválido.", 
            "data": None
        }, indent=4)
        
    except Exception as e:
        return json.dumps({
            "status": "error", 
            "message": f"Fallo en el proceso de firma: {str(e)}", 
            "data": None
        }, indent=4)