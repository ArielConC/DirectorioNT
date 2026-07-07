import sqlite3
import hashlib

def actualizar_db():
    conn = sqlite3.connect('directorio.db')
    c = conn.cursor()
    
    # 1. Borramos la tabla vieja de usuarios
    c.execute("DROP TABLE IF EXISTS Usuarios")
    
    # 2. Creamos la nueva con Rol y Puesto
    c.execute('''CREATE TABLE Usuarios (
                    usuario TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    puesto TEXT
                )''')
    
    # 3. Creamos tu cuenta de Administrador principal
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT INTO Usuarios (usuario, password, rol, puesto) 
        VALUES (?, ?, ?, ?)
    """, ('admin', pwd_hash, 'Admin', 'Administrador del Sistema'))
    
    conn.commit()
    conn.close()
    print("✅ ¡Tabla de usuarios actualizada con Roles y Puestos!")

actualizar_db()