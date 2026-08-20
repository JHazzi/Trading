import sqlite3
import requests
import time
from datetime import datetime
import hashlib

DB_PATH = "data/market_data.db"

# REQUISITO LEGAL DE LA SEC: Debes declarar tu nombre o app y un email de contacto en el User-Agent.
# Esto evita que baneen tu IP (Límite oficial: 10 peticiones por segundo).
HEADERS = {
    "User-Agent": "QuantMarketBot joaquin@example.com" # Puedes cambiar el email por el tuyo
}

def obtener_mapeo_cik():
    """Descarga el mapeo oficial de Tickers a CIK de la SEC."""
    print("[*] Obteniendo diccionario de Tickers -> CIK desde la SEC...")
    url = "https://www.sec.gov/files/company_tickers.json"
    
    respuesta = requests.get(url, headers=HEADERS)
    respuesta.raise_for_status()
    datos = respuesta.json()
    
    mapeo = {}
    for idx, info in datos.items():
        # El CIK debe ser un string de exactamente 10 dígitos (rellenado con ceros a la izquierda)
        mapeo[info['ticker']] = str(info['cik_str']).zfill(10)
    return mapeo

def descargar_historial_8k(ticker, cik, conn):
    """Descarga el historial de Formularios 8-K (Eventos Críticos) para un CIK específico."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code != 200:
            return 0
            
        datos = respuesta.json()
        filings = datos.get("filings", {}).get("recent", {})
        
        if not filings:
            return 0
            
        formularios = filings.get("form", [])
        fechas_aceptacion = filings.get("acceptanceDateTime", [])
        descripciones = filings.get("primaryDocDescription", [])
        
        nuevos_registros = 0
        cursor = conn.cursor()
        
        for i in range(len(formularios)):
            # Solo nos interesan los Formularios 8-K (Eventos materiales de impacto inmediato)
            if formularios[i] == "8-K":
                dt_str = fechas_aceptacion[i]
                if not dt_str: continue
                
                try:
                    # El formato de la SEC es '2023-10-25T16:02:23.000Z'. Este es nuestro T0 absoluto.
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
                    
                titulo = f"SEC Form 8-K: {descripciones[i] if descripciones[i] else 'Reporte Corporativo Oficial'}"
                resumen = "Reporte 8-K (SEC EDGAR). Evento corporativo no programado de importancia crítica. Fuente primaria verificada."
                
                string_id = f"SEC_8K_{ticker}_{dt.isoformat()}"
                id_noticia = hashlib.md5(string_id.encode()).hexdigest()
                
                try:
                    # Inyectamos en la tabla de noticias.
                    # Asignamos importancia = 1.0 porque es Ground Truth (evita pasar por el filtro Regex).
                    cursor.execute('''
                        INSERT INTO noticias (id, ticker, timestamp, titulo, fuente, resumen, importancia)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (id_noticia, ticker, dt.isoformat(), titulo, "SEC EDGAR", resumen, 1.0))
                    nuevos_registros += 1
                except sqlite3.IntegrityError:
                    pass # Evita duplicados si corres el script varias veces
                    
        conn.commit()
        return nuevos_registros
        
    except Exception as e:
        print(f"    [!] Error de red al procesar {ticker} (CIK: {cik}): {e}")
        return 0

def ingesta_masiva_sec():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ticker FROM universo_tickers WHERE activo = 1")
    tickers_activos = [fila[0] for fila in cursor.fetchall()]
    
    if not tickers_activos:
        print("[!] El universo de tickers está vacío. Corre init_db.py y carga tu universo.")
        conn.close()
        return
        
    mapeo_cik = obtener_mapeo_cik()
    print(f"[*] Iniciando extracción de Ground Truth (SEC 8-K) para {len(tickers_activos)} activos...")
    
    total_8k = 0
    for ticker in tickers_activos:
        cik = mapeo_cik.get(ticker)
        if not cik:
            print(f"    [-] Saltando {ticker}: No se encontró CIK oficial.")
            continue
            
        # Throttling de seguridad para respetar el límite de 10 peticiones/seg de la SEC
        time.sleep(0.15) 
        
        registros = descargar_historial_8k(ticker, cik, conn)
        total_8k += registros
        if registros > 0:
            print(f"    [+] {ticker}: {registros} eventos 8-K indexados con T0 exacto.")
            
    print(f"\n[*] Extracción completada. Se añadieron {total_8k} eventos oficiales inmutables.")
    conn.close()

if __name__ == "__main__":
    ingesta_masiva_sec()