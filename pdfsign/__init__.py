"""
Librería PdfSign - Firma digital de documentos PDF con certificados PKCS#12
"""

from .pdf import validate_pdf, analyze_pdf
from .certificate import discover_certificates, get_certificate_info
from .signer import sign_pdf
from .exceptions import PdfSignError, InvalidPdfError, CertificateError, SignatureError

__version__ = "0.1.0"

# __all__ define qué funciones son públicas cuando alguien hace "from pdfsign import *"
__all__ = [
    "validate_pdf",
    "analyze_pdf",
    "discover_certificates",
    "get_certificate_info",
    "sign_pdf",
    "PdfSignError",
    "InvalidPdfError",
    "CertificateError",
    "SignatureError"
]