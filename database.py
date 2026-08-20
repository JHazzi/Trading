import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "data/market_data.db"

def init_db():
    """Inicializa el esquema relacional para precios y noticias."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Precios Intradiarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios (
            ticker TEXT,
            timestamp DATETIME,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, timestamp)
        )
    ''')
    
    # Tabla de Noticias (Materia prima para el NLP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id TEXT PRIMARY KEY,
            ticker TEXT,
            timestamp DATETIME,
            titulo TEXT,
            fuente TEXT,
            grado INTEGER DEFAULT NULL, 
            sentimiento REAL DEFAULT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def guardar_precios(df: pd.DataFrame, ticker: str):
    """Inserta el DataFrame de precios en SQLite."""
    conn = sqlite3.connect(DB_PATH)
    # Renombramos el índice para que coincida con la base de datos
    df = df.reset_index().rename(columns={'Datetime': 'timestamp', 'Open': 'open', 
                                          'High': 'high', 'Low': 'low', 
                                          'Close': 'close', 'Volume': 'volume'})
    df['ticker'] = ticker
    # Filtrar solo las columnas que nos importan
    df = df[['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # Usamos 'replace' o lógica de upsert (esto es una simplificación)
    df.to_sql('precios', conn, if_exists='append', index=False)
    conn.close()
    
if __name__ == "__main__":
    init_db()
    print("[+] Base de datos SQLite inicializada en data/market_data.db")