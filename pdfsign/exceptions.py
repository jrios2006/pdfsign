"""
Archivo: pdfsign/exceptions.py

Módulo de excepciones personalizadas para la librería PdfSign.

--- ¿Dónde están las respuestas de error? ---
Actualmente, la librería está diseñada para integrarse fácilmente en APIs, 
herramientas CLI o interfaces web. Por ello, la mayoría de los errores se 
capturan internamente en `pdf.py`, `certificate.py` y `signer.py`, y se 
devuelven de forma segura como respuestas JSON estructuradas:
{"status": "error", "message": "Descripción del fallo"}

Estas excepciones se definen aquí como base estructural para el futuro. 
Si la librería evoluciona para un uso estrictamente interno en scripts Python, 
se pueden reemplazar los `return json.dumps(...)` por `raise SignatureError(...)` 
para usar bloques `try/except` nativos.

--- ¿Por qué se usa 'pass'? ---
En Python, al crear una excepción personalizada, solo necesitamos heredar de 
la clase base `Exception`. Al heredar, la clase ya sabe cómo guardar y mostrar 
un mensaje de error. La palabra reservada `pass` se utiliza simplemente para 
indicarle a Python que la clase no necesita atributos ni lógica adicional; 
funciona puramente como una "etiqueta" para clasificar el tipo de fallo.
"""

class PdfSignError(Exception):
    """
    Excepción base para todos los errores de la librería pdfsign.
    Permite capturar cualquier error de la librería usando un solo bloque:
    except PdfSignError as e: ...
    """
    pass


class InvalidPdfError(PdfSignError):
    """
    Se lanza cuando el archivo destino no existe, su estructura binaria 
    está corrupta, o no contiene la cabecera mágica '%PDF-'.
    """
    pass


class CertificateError(PdfSignError):
    """
    Se lanza cuando hay problemas al leer el contenedor criptográfico (.p12/.pfx), 
    la contraseña proporcionada es incorrecta o no se encuentra la clave privada.
    """
    pass


class SignatureError(PdfSignError):
    """
    Se lanza cuando ocurre un fallo en el motor de pyHanko o cryptography 
    durante el proceso físico de inyección de la firma PAdES en el documento.
    """
    pass