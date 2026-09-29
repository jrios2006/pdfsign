"""
Archivo: pdfsign/certificate.py
Módulo de gestión y descubrimiento de certificados digitales.

Este módulo se encarga de interactuar con el sistema de archivos y la 
librería `cryptography` para buscar, abrir y extraer de forma segura 
la información pública de los contenedores PKCS#12 (.p12 y .pfx), 
asegurando que la clave privada nunca se exponga.
"""

import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


def load_config(config_path="config/config.json"):
    """
    Carga la configuración del sistema desde un archivo JSON.
    
    Si el archivo de configuración no existe en la ruta especificada, 
    proporciona una configuración por defecto para garantizar que la 
    aplicación pueda seguir funcionando.

    Args:
        config_path (str): Ruta relativa o absoluta al archivo de configuración.

    Returns:
        dict: Diccionario con los parámetros de configuración (rutas y extensiones).
    """
    if not os.path.exists(config_path):
        return {
            "certificates": {
                "search_paths": ["./certificados"], 
                "allowed_extensions": [".p12", ".pfx"]
            }
        }
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def discover_certificates(config_path="config/config.json") -> list:
    """
    Busca de forma recursiva certificados en las rutas definidas en la configuración.
    
    Resuelve rutas relativas y variables de entorno del usuario (como '~' en Linux/Mac).
    Filtra los resultados basándose en las extensiones permitidas (.p12, .pfx).

    Args:
        config_path (str): Ruta al archivo JSON de configuración.

    Returns:
        list: Lista de strings, donde cada string es la ruta absoluta a un 
              archivo de certificado encontrado.
    """
    config = load_config(config_path)
    search_paths = config["certificates"].get("search_paths", [])
    extensions = tuple(config["certificates"].get("allowed_extensions", [".p12", ".pfx"]))
    
    found_certs = []
    for path_str in search_paths:
        # Resolvemos el home del usuario (~) y obtenemos la ruta absoluta
        base_path = Path(os.path.expanduser(path_str)).resolve()
        
        # Saltamos rutas que no existen para evitar errores en tiempo de ejecución
        if not base_path.exists() or not base_path.is_dir():
            continue
            
        # Búsqueda recursiva (rglob) de archivos con extensiones válidas
        for file in base_path.rglob("*"):
            if file.suffix.lower() in extensions:
                found_certs.append(str(file))
                
    return found_certs


def get_certificate_info(file_path: str, password: str) -> str:
    """
    Abre un archivo de certificado, verifica su contraseña y extrae metadatos.
    
    Utiliza la librería `cryptography` para desencriptar el contenedor PKCS#12.
    Extrae el Common Name (CN) del titular y del emisor, así como las fechas de 
    validez, devolviendo toda la información estructurada.
    
    Admite contraseñas vacías pasando un string vacío ("").

    Args:
        file_path (str): Ruta al archivo .p12 o .pfx.
        password (str): Contraseña del contenedor criptográfico.

    Returns:
        str: Cadena en formato JSON con la estructura:
             - status: "success" o "error"
             - message: Descripción del resultado
             - data: Diccionario con la información pública del certificado 
                     (titular, emisor, validez, y confirmación de clave privada).
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "status": "error", 
            "message": f"Archivo no existe: {file_path}", 
            "data": None
        })

    try:
        with open(file_path, "rb") as f:
            p12_data = f.read()

        # cryptography requiere bytes. Si es string vacío, pasamos None/b'' (según versión)
        password_bytes = password.encode('utf-8') if password else None

        # Desencriptado del contenedor
        private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
            p12_data, 
            password_bytes
        )

        if certificate is None:
            return json.dumps({
                "status": "error", 
                "message": "No contiene certificado válido.", 
                "data": None
            })

        # Extracción del titular (Subject) a través de los OIDs estándar
        subject = certificate.subject
        cn_attributes = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        subject_name = cn_attributes[0].value if cn_attributes else "Nombre Desconocido"

        # Extracción de la Autoridad Certificadora (Issuer)
        issuer = certificate.issuer
        issuer_attributes = issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        issuer_name = issuer_attributes[0].value if issuer_attributes else "Emisor Desconocido"

        cert_data = {
            "file_info": {"filename": os.path.basename(file_path)},
            "subject_name": subject_name,
            "issuer_name": issuer_name,
            "valid_from": certificate.not_valid_before_utc.isoformat(),
            "valid_until": certificate.not_valid_after_utc.isoformat(),
            "has_private_key": private_key is not None
        }

        return json.dumps({
            "status": "success", 
            "message": "Certificado procesado.", 
            "data": cert_data
        }, indent=4)

    except ValueError:
        # ValueError es lanzado por cryptography al fallar el descifrado
        return json.dumps({
            "status": "error", 
            "message": "Contraseña incorrecta o archivo corrupto.", 
            "data": None
        }, indent=4)
    except Exception as e:
        return json.dumps({
            "status": "error", 
            "message": f"Error: {str(e)}", 
            "data": None
        }, indent=4)