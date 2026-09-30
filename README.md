# PdfSign (v0.2.0)

PdfSign es una librería y herramienta de línea de comandos (CLI) en Python diseñada para facilitar la firma digital de documentos PDF utilizando certificados digitales locales (`.p12` o `.pfx`). 

Implementa firmas estándar PAdES y soporta firmas incrementales, permitiendo que múltiples usuarios firmen el mismo documento sin romper la validez criptográfica de las firmas anteriores.

## 🚀 Características
*   **Firma Incremental:** Permite múltiples firmas en un solo PDF.
*   **Visados Visuales Apilados:** Inyecta sellos gráficos dinámicos que no se solapan.
*   **Validación Integrada:** Analiza PDFs para comprobar firmas previas y su integridad.
*   **Descubrimiento de Certificados:** Busca automáticamente archivos `.p12`/`.pfx` en rutas configurables.
*   **Salida Estructurada:** API interna basada en JSON para fácil integración con otros sistemas.

## 📦 Instalación

1. Clona o descarga el repositorio.
2. Instala las dependencias necesarias mediante `pip`:

```bash
pip install -r requirements.txt
```

*Dependencias principales: `pyhanko`, `cryptography`, `Pillow` y `asn1crypto`.*

## ⚙️ Configuración

El comportamiento de búsqueda de certificados y el formato visual de los sellos se define en `config/config.json`. 

```json
{
    "certificates": {
        "search_paths": [
            "./certificados",
            "~/.pdfsign/certs"
        ],
        "allowed_extensions": [".p12", ".pfx"]
    },
    "visual_signatures": {
        "icons_path": "./images",
        "default_width": 200,
        "default_height": 50,
        "margin": 10,
        "base_x": 20,
        "base_y": 20,
        "allowed_reasons": {
            "aprobado": "Aprobado",
            "visado": "Visado",
            "revisado": "Revisado",
            "rechazado": "Rechazado"
        }
    }
}
```

## 💻 Uso desde Línea de Comandos (CLI)

El archivo `main.py` proporciona una interfaz de terminal profesional para interactuar con la librería.

### 1. Listar certificados disponibles
Busca y muestra todos los certificados válidos encontrados en las rutas configuradas.
```bash
python main.py list-certs
```

### 2. Analizar un documento PDF
Lee un PDF y muestra su tamaño, metadatos y la lista de firmas incrustadas, verificando su integridad.
```bash
python main.py analyze ruta/al/documento.pdf
```

### 3. Firmar un documento (Visados e Invisibles)
Inyecta una firma digital en el PDF. El archivo original nunca se sobreescribe. Por defecto, se crea un sello visual de "Visado".

```bash
# Firma visual estándar (Visado)
python main.py sign origen.pdf certificado.pfx destino.pdf

# Firma visual indicando un motivo específico (aprobado, visado, revisado, rechazado)
python main.py sign origen.pdf certificado.pfx destino.pdf --reason aprobado

# Firma puramente criptográfica (sin recuadro visual)
python main.py sign origen.pdf certificado.pfx destino.pdf --invisible
```

## 🎨 Especificación Funcional: Visados Visuales

Para mantener el cumplimiento del estándar PDF y la validez criptográfica, PdfSign implementa una arquitectura específica para la inyección de sellos:

### 1. Prevención de Corrupción (Inyección en la Última Página)
En la arquitectura de un documento PDF, una firma digital interactiva es un *Widget de Anotación* vinculado a una única página. Si la librería modificara todas las páginas de un documento para añadir una marca de agua iterativa *después* de que un primer usuario haya firmado, el hash criptográfico de esa primera firma se rompería al detectar cambios estructurales. 
Por ello, PdfSign extrae el número total de páginas del documento original e inyecta el widget de la firma de forma segura **únicamente en la última página**.

### 2. Algoritmo de Apilamiento (Stacking Algorithm)
Para documentos multifirma, PdfSign evita que el sello de un firmante sobrescriba el de otro mediante un algoritmo dinámico. Antes de firmar, el motor analiza el documento para contar las firmas previas. Basándose en este número, calcula el desplazamiento vertical exacto (eje Y) aplicando la altura de la caja (50pt) y un margen (10pt), creando una columna ordenada de visados en el lateral del documento.

### 3. Tipos de Visado y Recursos
El sistema soporta diferentes estados representados con iconos que deben alojarse en la carpeta `images/`:
*   `aprobado.png`
*   `visado.png`
*   `revisado.png`
*   `rechazado.png`

## 📁 Estructura del Proyecto

```text
pdfsign/
├── config/
│   └── config.json         # Rutas de certificados y configuración visual
├── pdfsign/
│   ├── __init__.py         # API Pública (v0.2.0)
│   ├── certificate.py      # Extracción y descubrimiento (cryptography)
│   ├── visual.py           # Algoritmos de apilamiento y estilos gráficos
│   ├── signer.py           # Motor de firma PAdES (pyHanko + cryptography)
│   ├── pdf.py              # Análisis y validación de documentos
│   └── exceptions.py       # Excepciones base de la librería
├── utils/
│   └── setup_images.py     # Generador automático de iconos base
├── examples/               # Carpeta para documentos de prueba
├── images/                 # Iconos para sellos visuales
├── tests/                  # Scripts de validación y pruebas
├── main.py                 # Interfaz de CLI
├── requirements.txt        # Dependencias
└── README.md               # Documentación
```