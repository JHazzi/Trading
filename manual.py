import sqlite3
import pandas as pd
import requests
import io

DB_PATH = "data/market_data.db"

def cargar_sp500():
    print("[*] Descargando componentes del S&P 500...")
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Encabezado para evitar el bloqueo 403 de Wikipedia
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Envolvemos el texto en StringIO para evitar advertencias de deprecación en Pandas
    tabla = pd.read_html(io.StringIO(response.text))[0]
    
    # Limpiamos los símbolos (ej. BRK.B a BRK-B)
    tabla['Symbol'] = tabla['Symbol'].str.replace('.', '-', regex=False)
    
    tickers = tabla[['Symbol', 'Security', 'GICS Sector']].values.tolist()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insertamos los activos
    cursor.executemany('''
        INSERT OR IGNORE INTO universo_tickers (ticker, empresa, sector, activo)
        VALUES (?, ?, ?, 1)
    ''', tickers)
    
    conn.commit()
    conn.close()
    print(f"[+] Se cargaron {len(tickers)} empresas en el universo.")

if __name__ == "__main__":
    cargar_sp500()