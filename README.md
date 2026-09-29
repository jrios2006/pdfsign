# PdfSign

PdfSign es una librería y herramienta de línea de comandos (CLI) en Python diseñada para facilitar la firma digital de documentos PDF utilizando certificados digitales locales (`.p12` o `.pfx`). 

Implementa firmas estándar PAdES y soporta firmas incrementales, permitiendo que múltiples usuarios firmen el mismo documento sin romper la validez criptográfica de las firmas anteriores.

## 🚀 Características
*   **Firma Incremental:** Permite múltiples firmas en un solo PDF.
*   **Validación Integrada:** Analiza PDFs para comprobar firmas previas y su integridad.
*   **Descubrimiento de Certificados:** Busca automáticamente archivos `.p12`/`.pfx` en rutas configurables.
*   **Salida Estructurada:** API interna basada en JSON para fácil integración con otros sistemas.
*   **CLI Completa:** Utilizable directamente desde la terminal.

## 📦 Instalación

1. Clona o descarga el repositorio.
2. Instala las dependencias necesarias mediante `pip`:

```bash
pip install -r requirements.txt
```

*Dependencias principales: `pyhanko`, `cryptography` y `asn1crypto`.*

## ⚙️ Configuración

El comportamiento de búsqueda de certificados se define en `config/config.json`. Puedes añadir las rutas donde guardas tus certificados (incluso rutas relativas o con `~` para el directorio de usuario).

```json
{
    "certificates": {
        "search_paths": [
            "./certificados",
            "~/.pdfsign/certs"
        ],
        "allowed_extensions": [".p12", ".pfx"]
    }
}
```

## 🔐 Generar Certificado de Prueba (OpenSSL)

Si no dispones de un certificado real (como los de la FNMT) y quieres hacer pruebas locales, puedes generar un certificado autofirmado en formato `.p12` utilizando OpenSSL.

Ejecuta estos comandos en la raíz del proyecto. El sistema generará un certificado con la contraseña **`prueba123`** y lo guardará en la carpeta `certificados/`:

```bash
# 1. Crear el directorio si no existe
mkdir -p certificados

# 2. Generar clave privada y certificado (válido por 1 año)
openssl req -x509 -newkey rsa:2048 -keyout certificados/clave_temp.pem -out certificados/cert_temp.pem -days 365 -nodes -subj "/CN=Usuario De Prueba OpenSSL/O=Proyecto PdfSign"

# 3. Empaquetar ambos en un archivo .p12 con la contraseña "prueba123"
openssl pkcs12 -export -out certificados/prueba_local.p12 -inkey certificados/clave_temp.pem -in certificados/cert_temp.pem -passout pass:prueba123

# 4. Eliminar los archivos temporales PEM
rm certificados/clave_temp.pem certificados/cert_temp.pem
```

## 💻 Uso desde Línea de Comandos (CLI)

El archivo `main.py` proporciona una interfaz de terminal profesional para interactuar con la librería.

### 1. Listar certificados disponibles
Busca y muestra todos los certificados válidos encontrados en las rutas del `config.json`.
```bash
python main.py list-certs
```

### 2. Analizar un documento PDF
Lee un PDF y muestra su tamaño, metadatos y la lista de firmas incrustadas, verificando su integridad.
```bash
python main.py analyze ruta/al/documento.pdf
```

### 3. Firmar un documento
Inyecta una firma digital en el PDF. Te solicitará la contraseña de forma segura en la terminal. El archivo original nunca se sobreescribe.
```bash
python main.py sign archivo_original.pdf ruta/al/certificado.pfx archivo_firmado.pdf
```

## 🛠️ Uso como Librería Python

PdfSign está diseñado para ser importado fácilmente en otros proyectos Python. Todas sus funciones devuelven un string en formato JSON con la estructura `status`, `message` y `data`.

```python
import json
from pdfsign import sign_pdf, analyze_pdf

# 1. Analizar un PDF
analisis_json = analyze_pdf("contrato.pdf")
resultado = json.loads(analisis_json)

if resultado["status"] == "success":
    print("Firmas actuales:", resultado["data"]["signatures"])

# 2. Firmar un PDF
firma_json = sign_pdf(
    input_pdf="contrato.pdf",
    cert_path="certificados/usuario.p12",
    password="mi_contraseña_segura",
    output_pdf="contrato_firmado.pdf"
)

respuesta = json.loads(firma_json)
if respuesta["status"] == "success":
    print("Documento firmado correctamente por:", respuesta["data"]["signer_name"])
else:
    print("Error:", respuesta["message"])
```

## 📁 Estructura del Proyecto

```text
pdfsign/
├── config/
│   └── config.json         # Rutas de certificados
├── pdfsign/
│   ├── __init__.py         # Exportación de módulos
│   ├── certificate.py      # Extracción y descubrimiento (cryptography)
│   ├── signer.py           # Motor de firma PAdES (pyHanko + cryptography)
│   ├── pdf.py              # Análisis y validación de documentos
│   └── exceptions.py       # Excepciones base de la librería
├── examples/               # Carpeta para documentos de prueba
├── tests/                  # Scripts de validación y pruebas
├── main.py                 # Interfaz de Línea de Comandos (CLI)
├── requirements.txt        # Dependencias
└── README.md               # Documentación
```