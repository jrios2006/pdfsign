"""
Librería PdfSign - Firma digital de documentos PDF con certificados PKCS#12

Este módulo de inicialización define la API pública del paquete `pdfsign`.
Al importar funciones de este paquete (ej. `from pdfsign import sign_pdf`), 
este archivo se encarga de exponer solo los componentes esenciales, ocultando 
la complejidad interna y los submódulos.

Componentes expuestos:
- Validación y análisis: `validate_pdf`, `analyze_pdf`
- Gestión de certificados: `discover_certificates`, `get_certificate_info`
- Generación visual: `calculate_signature_box`, `create_stamp_style`
- Motor criptográfico: `sign_pdf`
- Excepciones base: `PdfSignError` y sus derivadas.
"""

from .pdf import validate_pdf, analyze_pdf
from .certificate import discover_certificates, get_certificate_info
from .visual import calculate_signature_box, create_stamp_style
from .signer import sign_pdf
from .exceptions import PdfSignError, InvalidPdfError, CertificateError, SignatureError

__version__ = "0.2.0"

# __all__ define qué funciones son públicas cuando alguien hace "from pdfsign import *"
__all__ = [
    "validate_pdf",
    "analyze_pdf",
    "discover_certificates",
    "get_certificate_info",
    "calculate_signature_box",
    "create_stamp_style",
    "sign_pdf",
    "PdfSignError",
    "InvalidPdfError",
    "CertificateError",
    "SignatureError"
]