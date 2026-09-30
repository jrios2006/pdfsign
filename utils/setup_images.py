"""
Archivo: utils/setup_images.py

Script de utilidad para la generación automática de iconos de visado.

--- Propósito del script ---
Este módulo no forma parte del núcleo criptográfico de PdfSign. Se 
proporciona como una herramienta de desarrollo para generar rápidamente 
los recursos gráficos (imágenes PNG con transparencia) necesarios para 
probar el módulo de firmas visuales.

Al ejecutar este script, calculará la ruta al directorio raíz del proyecto,
creará la carpeta 'images/' si no existe, y generará iconos base para 
los estados: Aprobado, Visado, Revisado y Rechazado.

Uso recomendado desde la raíz del proyecto:
    python utils/setup_images.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Calculamos dinámicamente la ruta raíz del proyecto (un nivel por encima de utils/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IMAGES_DIR = os.path.join(BASE_DIR, "images")


def create_stamp_icon(filename: str, color: tuple, text: str, size: tuple = (100, 100)):
    """
    Genera un icono circular simple con una letra o símbolo en el centro.
    
    Utiliza la librería Pillow (PIL) para crear un lienzo RGBA con fondo 
    transparente. Dibuja un contorno circular y centra tipográficamente 
    el carácter proporcionado.

    Args:
        filename (str): Nombre del archivo resultante (ej. 'aprobado.png').
        color (tuple): Tupla RGB que define el color del trazo y el texto.
        text (str): Símbolo o inicial que se mostrará en el centro.
        size (tuple): Dimensiones de la imagen generada (ancho, alto).
    """
    # Crear imagen con fondo 100% transparente
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Dibujar círculo exterior
    margin = 5
    draw.ellipse(
        [(margin, margin), (size[0]-margin, size[1]-margin)], 
        outline=color, 
        width=8
    )
    
    # Cargar fuente (Intenta usar Arial, si falla usa la predeterminada de PIL)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
        
    # Calcular dimensiones del texto para el centrado
    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # Fallback para versiones antiguas de Pillow
        text_w, text_h = draw.textsize(text, font=font)
    
    x = (size[0] - text_w) / 2
    y = (size[1] - text_h) / 2 - 10 
    
    # Inyectar texto y guardar archivo
    draw.text((x, y), text, font=font, fill=color)
    
    filepath = os.path.join(IMAGES_DIR, filename)
    img.save(filepath, "PNG")
    print(f"✅ Generado: {filepath}")


def main():
    """
    Función principal de orquestación.
    Crea el directorio de destino y ejecuta la generación iterativa de iconos.
    """
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    iconos = [
        ("aprobado.png", (46, 204, 113), "A"),  # Verde
        ("visado.png", (52, 152, 219), "V"),    # Azul
        ("revisado.png", (230, 126, 34), "R"),  # Naranja
        ("rechazado.png", (231, 76, 60), "X")   # Rojo
    ]
    
    print(f"Generando iconos de prueba en: {IMAGES_DIR} ...")
    for filename, color, text in iconos:
        create_stamp_icon(filename, color, text)
        
    print("\n¡Iconos listos! Ahora tienes la carpeta 'images/' preparada en la raíz.")


if __name__ == "__main__":
    main()