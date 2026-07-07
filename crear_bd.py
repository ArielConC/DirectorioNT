import sqlite3

# 1. Conectar a la base de datos (esto crea el archivo 'directorio.db' automáticamente)
conexion = sqlite3.connect('directorio.db')
cursor = conexion.cursor()

# 2. Crear las tablas
cursor.execute('''
CREATE TABLE IF NOT EXISTS Empresas (
    id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    sector TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Ubicaciones (
    id_ubicacion INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('Nacional', 'Internacional')),
    pais TEXT NOT NULL,
    estado TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Contactos (
    id_contacto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    puesto TEXT,
    correo TEXT,
    telefono TEXT,
    id_empresa INTEGER,
    id_ubicacion INTEGER,
    FOREIGN KEY (id_empresa) REFERENCES Empresas(id_empresa),
    FOREIGN KEY (id_ubicacion) REFERENCES Ubicaciones(id_ubicacion)
)
''')

# 3. Guardar cambios y cerrar la conexión
conexion.commit()
conexion.close()

print("¡Base de datos y tablas creadas con éxito!")