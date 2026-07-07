import pytesseract
from PIL import Image
import os
import re
import sqlite3 # <-- Nueva librería para conectarnos a la base de datos

# --- CONFIGURACIÓN PARA WINDOWS ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
ruta_imagen = 'tarjetas/prueba1.jpg'

try:
    imagen = Image.open(ruta_imagen)
    
    # 1. Redimensionar
    ancho_base = 1000
    proporcion = (ancho_base / float(imagen.size[0]))
    alto = int((float(imagen.size[1]) * float(proporcion)))
    imagen = imagen.resize((ancho_base, alto), Image.Resampling.LANCZOS)
    
    # 2. Rotar si es necesario
    ancho, alto = imagen.size
    if alto > ancho:
        imagen = imagen.rotate(90, expand=True)
        
    # 3. Filtros
    imagen = imagen.convert('L')
    umbral = 140
    imagen = imagen.point(lambda p: 255 if p > umbral else 0, mode='1')
    
    # 4. Leer texto bruto
    texto_extraido = pytesseract.image_to_string(imagen, config=r'--psm 6')
    
    # 5. MAGIA REGEX: Buscar el correo
    correos = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', texto_extraido)
    correo_limpio = correos[0] if correos else ""
        
    # 6. MAGIA REGEX: Buscar el teléfono
    telefonos = re.findall(r'\(?\+?\d{1,3}\)?[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{4}', texto_extraido)
    telefono_limpio = telefonos[0] if telefonos else ""

    print(f"📧 Correo encontrado: {correo_limpio}")
    print(f"📱 Teléfono encontrado: {telefono_limpio}")

    # ==========================================
    # 7. NUEVO PASO: GUARDAR EN BASE DE DATOS
    # ==========================================
    
    # Solo guardamos si encontró al menos un dato útil
    if correo_limpio or telefono_limpio:
        # Generar un nombre temporal si no lo tenemos
        nombre_temporal = correo_limpio.split('@')[0] if correo_limpio else "Contacto sin nombre"
        
        # Conectar a la base de datos
        conexion = sqlite3.connect('directorio.db')
        cursor = conexion.cursor()
        
        # Insertar los datos
        cursor.execute('''
            INSERT INTO Contactos (nombre_completo, correo, telefono)
            VALUES (?, ?, ?)
        ''', (nombre_temporal, correo_limpio, telefono_limpio))
        
        # Confirmar los cambios y cerrar
        conexion.commit()
        conexion.close()
        
        print("✅ ¡Los datos de la tarjeta se guardaron exitosamente en SQLite!")
    else:
        print("⚠️ No se encontraron datos útiles para guardar en esta tarjeta.")

except Exception as e:
    print(f"Ocurrió un error: {e}")