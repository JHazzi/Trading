import sqlite3
import requests
import time
from datetime import datetime
import hashlib
import re
from bs4 import BeautifulSoup

DB_PATH = "data/market_data.db"
HEADERS = {
    "User-Agent": "QuantMarketBot joaquin@example.com" # Cambia esto por tu email
}

def obtener_mapeo_cik():
    print("[*] Obteniendo diccionario de Tickers -> CIK desde la SEC...")
    url = "https://www.sec.gov/files/company_tickers.json"
    respuesta = requests.get(url, headers=HEADERS)
    respuesta.raise_for_status()
    mapeo = {}
    for idx, info in respuesta.json().items():
        mapeo[info['ticker']] = str(info['cik_str']).zfill(10)
    return mapeo

def limpiar_html_sec(html_content):
    """Filtra el ruido legal/visual y extrae el texto corporativo puro saltando la portada."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Destruimos las tablas financieras, scripts y estilos
    for element in soup(["table", "style", "script", "meta", "noscript", "header", "footer"]):
        element.decompose()
        
    # 2. Extraemos el texto y limpiamos espacios múltiples
    texto = soup.get_text(separator=' ')
    texto_limpio = re.sub(r'\s+', ' ', texto).strip()
    
    # 3. CAZA DE LA NOTICIA REAL (Regex)
    # Buscamos el patrón "Item X.XX" (ej. Item 1.01 o ITEM 8.01) que marca el inicio de la noticia
    match = re.search(r'Item\s+\d\.\d{2}', texto_limpio, flags=re.IGNORECASE)
    
    if match:
        # Si encuentra el Item, cortamos la portada y tomamos los siguientes 2000 caracteres
        inicio = match.start()
        resumen_real = texto_limpio[inicio : inicio + 2000]
    else:
        # Fallback: Si el formato es raro, nos saltamos los primeros 1500 caracteres a ciegas
        resumen_real = texto_limpio[1500 : 3500]
        
    # Limpiamos un poco más el resumen final
    resumen_real = re.sub(r'\s+', ' ', resumen_real).strip() + "..."
    
    return texto_limpio, resumen_real

def descargar_historial_8k(ticker, cik, conn):
    url_meta = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    try:
        respuesta = requests.get(url_meta, headers=HEADERS)
        if respuesta.status_code != 200:
            return 0
            
        filings = respuesta.json().get("filings", {}).get("recent", {})
        if not filings: return 0
        
        formularios = filings.get("form", [])
        fechas = filings.get("acceptanceDateTime", [])
        descripciones = filings.get("primaryDocDescription", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])
        
        nuevos_registros = 0
        cursor = conn.cursor()
        
        for i in range(len(formularios)):
            if formularios[i] == "8-K":
                dt_str = fechas[i]
                acc_num = accession_numbers[i]
                doc_file = primary_docs[i]
                
                if not dt_str or not acc_num or not doc_file: 
                    continue
                    
                # La SEC exige quitar los ceros a la izquierda del CIK y los guiones del accessionNumber para los archivos
                cik_archivo = str(int(cik))
                acc_num_limpio = acc_num.replace("-", "")
                url_documento = f"https://www.sec.gov/Archives/edgar/data/{cik_archivo}/{acc_num_limpio}/{doc_file}"
                
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    
                    # --- DEEP SCRAPING ---
                    # Hacemos una pausa para respetar el límite de la API
                    time.sleep(0.01) 
                    doc_resp = requests.get(url_documento, headers=HEADERS)
                    
                    if doc_resp.status_code == 200:
                        texto_completo, resumen = limpiar_html_sec(doc_resp.text)
                        print(f"      [+] {ticker} | {dt.date()} | Éxito: {len(texto_completo)} chars totales. Resumen: {resumen[:1000]}...")
                    else:
                        print(f"      [-] {ticker} | Error 404 al intentar descargar el documento físico.")
                        continue
                        
                except Exception as e:
                    print(f"      [!] Error procesando archivo de {ticker}: {e}")
                    continue
                    
                titulo = f"SEC Form 8-K: {descripciones[i] if descripciones[i] else 'Reporte Corporativo'}"
                string_id = f"SEC_8K_{ticker}_{dt.isoformat()}"
                id_noticia = hashlib.md5(string_id.encode()).hexdigest()
                
                try:
                    cursor.execute('''
                        INSERT INTO noticias (id, ticker, timestamp, titulo, fuente, resumen, importancia)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (id_noticia, ticker, dt.isoformat(), titulo, "SEC EDGAR", resumen, 1.0))
                    nuevos_registros += 1
                except sqlite3.IntegrityError:
                    pass 
                    
        conn.commit()
        return nuevos_registros
        
    except Exception as e:
        print(f"    [!] Error de red al procesar metadatos de {ticker}: {e}")
        return 0

def ingesta_masiva_sec():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ticker FROM universo_tickers WHERE activo = 1")
    tickers = [fila[0] for fila in cursor.fetchall()]
    
    if not tickers:
        print("[!] Universo vacío.")
        return
        
    mapeo_cik = obtener_mapeo_cik()
    print(f"[*] Iniciando Deep Scraping (SEC 8-K) para {len(tickers)} activos...")
    print(f"[*] Esto tomará tiempo debido a la descarga y parseo de HTMLs en crudo...\n")
    
    total = 0
    for ticker in tickers:
        cik = mapeo_cik.get(ticker)
        if not cik: continue
            
        time.sleep(0.01)
        print(f"  -> Rastreando {ticker}...")
        registros = descargar_historial_8k(ticker, cik, conn)
        total += registros
            
    print(f"\n[*] Extracción profunda completada. Se inyectaron {total} documentos con texto real.")
    conn.close()

if __name__ == "__main__":
    ingesta_masiva_sec()