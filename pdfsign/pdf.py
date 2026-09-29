"""
Archivo: pdfsign/pdf.py

Módulo de análisis y validación de documentos PDF.

Este módulo utiliza la librería `pyHanko` para realizar dos tareas principales:
1. Validar la integridad estructural de un archivo para confirmar que es un PDF válido.
2. Analizar el contenido del documento, extrayendo metadatos y verificando las 
   firmas digitales incrustadas (PAdES). Gestiona de forma controlada los errores de 
   validación de confianza (ej. certificados autofirmados o falta de CA raíz) para 
   no interrumpir la ejecución del programa.
"""

import os
import json
import logging
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.pdf_utils.misc import PdfReadError

# Silenciamos logs de error internos de pyHanko.
# Esto evita que los certificados autofirmados o sin cadena de confianza instalada 
# en el sistema operativo impriman Tracebacks gigantes ("ruido") en la consola.
logging.getLogger("pyhanko.sign.validation").setLevel(logging.CRITICAL)
logging.getLogger("pyhanko_certvalidator").setLevel(logging.CRITICAL)


def validate_pdf(file_path: str) -> dict:
    """
    Verifica que el archivo exista, sea accesible y tenga una estructura PDF válida.
    
    Realiza una comprobación de bajo nivel leyendo los primeros bytes para 
    verificar la cabecera mágica ('%PDF-') y luego intenta analizar la raíz 
    del documento utilizando pyHanko.

    Args:
        file_path (str): Ruta al archivo que se desea validar.

    Returns:
        dict: Un diccionario con el resultado de la validación:
              - is_valid (bool): True si es un PDF correcto, False en caso contrario.
              - error (str | None): Mensaje descriptivo si ocurre un fallo.
              - file_path (str): La ruta evaluada.
    """
    response = {"is_valid": False, "error": None, "file_path": file_path}

    if not os.path.exists(file_path):
        response["error"] = "El archivo no existe en la ruta especificada."
        return response

    try:
        with open(file_path, 'rb') as f:
            # Comprobación de cabecera mágica
            header = f.read(5)
            if header != b'%PDF-':
                response["error"] = "El archivo no tiene la cabecera PDF válida."
                return response
            
            # Intento de lectura estructural
            f.seek(0)
            reader = PdfFileReader(f)
            _ = reader.root 
            
        response["is_valid"] = True
        
    except PdfReadError as e:
        response["error"] = f"El archivo tiene un formato PDF inválido o corrupto: {str(e)}"
    except Exception as e:
        response["error"] = f"Error inesperado al validar: {str(e)}"
        
    return response


def analyze_pdf(file_path: str) -> str:
    """
    Analiza la estructura de un PDF y extrae información sobre sus firmas y metadatos.
    
    Este proceso consta de dos fases para las firmas:
    1. Extracción directa: Lee el nombre del firmante directamente de los bytes 
       del certificado para asegurar que siempre se recupere la información.
    2. Validación criptográfica: Intenta verificar matemáticamente la integridad 
       del documento (si ha sido modificado) y la confianza del certificado.

    Args:
        file_path (str): Ruta al documento PDF.

    Returns:
        str: Cadena en formato JSON con la estructura estándar (status, message, data).
             En 'data' incluye el tamaño del archivo, un diccionario de metadatos 
             y una lista de firmas detectadas con su estado de integridad.
    """
    validation = validate_pdf(file_path)
    if not validation["is_valid"]:
        return json.dumps({
            "status": "error", 
            "message": validation["error"], 
            "data": None
        }, indent=4)

    analysis_data = {
        "file_info": {
            "size_bytes": os.path.getsize(file_path),
            "filename": os.path.basename(file_path)
        },
        "signatures": [],
        "metadata": {}
    }

    try:
        with open(file_path, 'rb') as f:
            reader = PdfFileReader(f)
            
            # --- Extraer firmas ---
            embedded_sigs = reader.embedded_signatures
            if embedded_sigs:
                for sig in embedded_sigs:
                    # 1. Extraer nombre DIRECTAMENTE del certificado incrustado (sin validar confianza)
                    signer_name = "Firmante Desconocido"
                    try:
                        if sig.signer_cert:
                            signer_name = sig.signer_cert.subject.human_friendly
                    except Exception:
                        pass
                    
                    # 2. Intentar validar integridad y confianza
                    is_intact = "No verificada"
                    try:
                        status = validate_pdf_signature(sig)
                        is_intact = status.intact
                    except Exception:
                        # Si falla, normalmente es porque la CA raíz no está en el SO
                        is_intact = "Integridad no verificable (Falta CA raíz en el sistema)"

                    analysis_data["signatures"].append({
                        "field_name": sig.field_name,
                        "signer_name": signer_name,
                        "is_intact": is_intact,
                        "signature_date": str(sig.sig_object.get('/M', 'No disponible')) 
                    })

            # --- Extraer metadatos ---
            if '/Info' in reader.trailer:
                info = reader.trailer['/Info']
                for key, value in info.items():
                    clean_key = key.strip('/')
                    analysis_data["metadata"][clean_key] = str(value)

        return json.dumps({
            "status": "success",
            "message": "Análisis completado correctamente",
            "data": analysis_data
        }, indent=4, ensure_ascii=False)

    except Exception as e:
         return json.dumps({
             "status": "error", 
             "message": f"Error crítico al analizar el documento: {str(e)}", 
             "data": None
         }, indent=4)