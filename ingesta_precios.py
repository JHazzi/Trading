import yfinance as yf
import pandas as pd
import os

def descargar_datos_intradiarios(ticker: str, intervalo: str = "5m", periodo: str = "60d"):
    """
    Descarga datos intradiarios de un activo.
    Nota: yfinance limita los datos de 5 minutos a un máximo de 60 días históricos.
    """
    print(f"[*] Conectando al mercado para obtener {ticker} (Intervalo: {intervalo})...")
    
    # El objeto Ticker maneja la conexión con el endpoint
    activo = yf.Ticker(ticker)
    
    # Descargamos el dataframe
    df = activo.history(period=periodo, interval=intervalo)
    
    if df.empty:
        print(f"[!] Error: No se encontraron datos para {ticker}.")
        return None
        
    # Limpiamos zonas horarias para evitar problemas en la base de datos más adelante
    df.index = df.index.tz_localize(None)
    
    # Creamos un directorio para los datos si no existe
    os.makedirs("data/raw", exist_ok=True)
    
    # Persistencia temporal en CSV
    ruta_archivo = f"data/raw/{ticker}_{intervalo}.csv"
    df.to_csv(ruta_archivo)
    
    print(f"[+] Éxito. {len(df)} registros guardados en {ruta_archivo}")
    return df

if __name__ == "__main__":
    # Prueba con Apple, como mencionamos en el grafo y los axiomas
    datos = descargar_datos_intradiarios("AAPL", intervalo="5m", periodo="60d")
    
    if datos is not None:
        print("\nMuestra de los últimos 3 registros obtenidos:")
        print(datos[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))