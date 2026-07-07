import sqlite3

try:
    conn = sqlite3.connect('directorio.db')
    c = conn.cursor()
    # Agregamos la columna 'telefono_2' a la tabla que ya existe
    c.execute("ALTER TABLE Contactos ADD COLUMN telefono_2 TEXT")
    conn.commit()
    print("✅ ¡Columna 'telefono_2' agregada exitosamente a la base de datos!")
except sqlite3.OperationalError:
    print("⚠️ La columna 'telefono_2' ya existe o hubo un problema. No se hicieron cambios.")
finally:
    conn.close()