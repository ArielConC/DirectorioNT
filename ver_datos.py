import sqlite3
import pandas as pd

conexion = sqlite3.connect('directorio.db')
df = pd.read_sql_query("SELECT * FROM Contactos", conexion)
print(df)