import sqlite3

conn = sqlite3.connect('directorio.db')
c = conn.cursor()

# Agregamos un par de empresas de prueba
c.executemany("INSERT INTO Empresas (nombre, sector) VALUES (?, ?)", [
    ('Tech Solutions', 'Tecnología'),
    ('Manufacturas del Norte', 'Industria'),
    ('Servicios Globales', 'Consultoría')
])

# Agregamos ubicaciones de prueba (Nacionales e Internacionales)
c.executemany("INSERT INTO Ubicaciones (tipo, pais, estado) VALUES (?, ?, ?)", [
    ('Nacional', 'México', 'Guanajuato'),
    ('Nacional', 'México', 'Jalisco'),
    ('Nacional', 'México', 'CDMX'),
    ('Internacional', 'Estados Unidos', 'California'),
    ('Internacional', 'España', 'Madrid')
])

conn.commit()
conn.close()
print("¡Catálogos de Empresas y Ubicaciones listos!")