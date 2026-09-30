"""
Archivo: pdfsign/visual.py

Módulo para la generación de sellos visuales (visados) en documentos PDF.

--- Propósito del módulo ---
Este módulo abstrae toda la lógica gráfica y de posicionamiento de las firmas.
Contiene el algoritmo de apilamiento (Stacking Algorithm) para asegurar que 
las firmas múltiples no se superpongan en el documento, y genera el estilo 
visual (TextStampStyle) que pyHanko utilizará para renderizar el recuadro.

--- Comportamiento de Varias Hojas ---
En el estándar PDF, el campo de firma digital (Widget) debe pertenecer a una 
página específica. Este módulo calcula las coordenadas, pero será el motor en 
`signer.py` quien decidirá inyectar este recuadro en la última página del 
documento, iterando previamente si fuera necesario añadir marcas de agua.
"""

import os
import json
from pyhanko.stamp import TextStampStyle
from pyhanko.pdf_utils.images import PdfImage  # <-- Usamos el gestor de imágenes de pyHanko

def load_visual_config(config_path: str = "config/config.json") -> dict:
    """
    Carga de forma segura la sección visual de la configuración del sistema.
    Si el archivo o la sección no existen, devuelve valores por defecto.
    """
    default_config = {
        "icons_path": "./images",
        "default_width": 200,
        "default_height": 50,
        "margin": 10,
        "base_x": 20,
        "base_y": 20
    }
    
    if not os.path.exists(config_path):
        return default_config
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("visual_signatures", default_config)
    except Exception:
        return default_config


def calculate_signature_box(num_signatures: int, config_path: str = "config/config.json") -> tuple:
    """
    Algoritmo de apilamiento (Stacking) para firmas múltiples.
    
    Calcula las coordenadas físicas en la página donde se dibujará el sello.
    El punto de origen (0,0) en los PDF suele ser la esquina inferior izquierda.
    Al multiplicar el número de firmas previas por el alto del sello y el margen,
    logramos que cada nueva firma se apile dinámicamente encima de la anterior.

    Args:
        num_signatures (int): Número de firmas que ya existen en el documento.
        config_path (str): Ruta al archivo de configuración.

    Returns:
        Box: Objeto de pyHanko que define el rectángulo (X1, Y1, X2, Y2).
    """
    config = load_visual_config(config_path)
    
    base_x = config.get("base_x", 20)
    base_y = config.get("base_y", 20)
    width = config.get("default_width", 200)
    height = config.get("default_height", 50)
    margin = config.get("margin", 10)

    # Algoritmo de apilamiento vertical
    y1 = base_y + (num_signatures * (height + margin))
    y2 = y1 + height
    x1 = base_x
    x2 = x1 + width

    return (x1, y1, x2, y2)


def create_stamp_style(reason: str, config_path: str = "config/config.json") -> TextStampStyle:
    """
    Genera el estilo visual del sello combinando texto y metadatos con el 
    icono de fondo correspondiente al estado (Aprobado, Visado, etc.).

    Args:
        reason (str): El motivo del visado.
        config_path (str): Ruta al archivo de configuración.

    Returns:
        TextStampStyle: Objeto de estilo que pyHanko usará para renderizar.
    """
    config = load_visual_config(config_path)
    icons_path = config.get("icons_path", "./images")
    
    reason_key = reason.lower() if reason else "visado"
    icon_filename = f"{reason_key}.png"
    icon_full_path = os.path.join(icons_path, icon_filename)
    
    bg_image = None
    if os.path.exists(icon_full_path):
        # Envolvemos la imagen en el formato que pyHanko puede escribir en el PDF
        bg_image = PdfImage(icon_full_path)
        
    texto_sello = (
        "FIRMADO POR: %(signer)s\n"
        f"MOTIVO: {reason}\n"
        "FECHA: %(ts)s"
    )

    style = TextStampStyle(
        stamp_text=texto_sello,
        background=bg_image,
        background_opacity=0.25,
        timestamp_format='%d/%m/%Y %H:%M:%S'
    )
    
    return style