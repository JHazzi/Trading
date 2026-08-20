import sqlite3
import torch
import re
from transformers import pipeline

DB_PATH = "data/market_data.db"
BATCH_SIZE = 16

def limpiar_nombre_empresa(nombre_crudo: str) -> str:
    """Elimina sufijos legales para facilitar el cruce (ej. 'Apple Inc.' -> 'Apple')."""
    if not nombre_crudo: return ""
    sufijos = r'\b(inc|corp|corporation|llc|plc|ltd|company|co)\b\.?'
    nombre_limpio = re.sub(sufijos, '', nombre_crudo.lower(), flags=re.IGNORECASE)
    # Limpiamos espacios extra y caracteres especiales
    return re.sub(r'[^a-z0-9\s]', '', nombre_limpio).strip()

def cargar_universo_empresas(conn):
    """Carga el universo y crea un diccionario de nombres limpios hacia Tickers."""
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, empresa FROM universo_tickers WHERE activo = 1")
    universo = {}
    for ticker, nombre in cursor.fetchall():
        nombre_limpio = limpiar_nombre_empresa(nombre)
        if nombre_limpio:
            universo[nombre_limpio] = ticker
    return universo

def mineria_entidades_retroactiva():
    device_id = 0 if torch.cuda.is_available() else -1
    print(f"[*] Aceleración por hardware (NER): {'Activada' if device_id == 0 else 'Desactivada'}")
    print("[*] Cargando modelo NER (Named Entity Recognition)...")
    
    # aggregation_strategy="simple" agrupa las sub-palabras ("Micro" + "soft" = "Microsoft")
    reconocedor_entidades = pipeline(
        "ner", 
        model="dslim/bert-base-NER", 
        aggregation_strategy="simple", 
        device=device_id
    )

    conn = sqlite3.connect(DB_PATH)
    universo_dict = cargar_universo_empresas(conn)
    
    # Solo procesamos noticias de la SEC que no hayan aportado al grafo todavía
    df_noticias = conn.execute("""
        SELECT id, ticker, timestamp, resumen 
        FROM noticias 
        WHERE importancia = 1.0
    """).fetchall()

    if not df_noticias:
        print("[!] No se encontraron textos para procesar.")
        conn.close()
        return

    print(f"[*] Escaneando {len(df_noticias)} documentos históricos en busca de menciones cruzadas...")
    
    nuevas_relaciones = []
    cursor = conn.cursor()

    for i in range(0, len(df_noticias), BATCH_SIZE):
        lote = df_noticias[i : i + BATCH_SIZE]
        textos = [fila[3] if fila[3] else "Empty." for fila in lote]
        
        try:
            resultados_ner = reconocedor_entidades(textos)
            
            for idx, entidades_texto in enumerate(resultados_ner):
                ticker_origen = lote[idx][1]
                fecha_origen = lote[idx][2]
                
                # Manejo de listas de entidades (si hay una o varias)
                if isinstance(entidades_texto, dict):
                    entidades_texto = [entidades_texto]
                
                empresas_encontradas = set()
                
                for entidad in entidades_texto:
                    # Filtramos solo lo que la IA detecta como Organización (ORG)
                    if entidad.get('entity_group') == 'ORG':
                        org_cruda = entidad.get('word', '')
                        org_limpia = limpiar_nombre_empresa(org_cruda)
                        
                        # Si la organización mencionada es larga (evita falsos positivos cortos)
                        if len(org_limpia) > 2:
                            # Cruzamos con nuestro universo
                            for nombre_universo, ticker_destino in universo_dict.items():
                                if nombre_universo in org_limpia or org_limpia in nombre_universo:
                                    if ticker_destino != ticker_origen:
                                        empresas_encontradas.add(ticker_destino)
                
                for ticker_destino in empresas_encontradas:
                    nuevas_relaciones.append((ticker_origen, ticker_destino, fecha_origen))
                    
        except Exception as e:
            print(f"  [!] Error procesando lote NER: {e}")
            continue
            
        if i % 1600 == 0 and i > 0:
            print(f"  -> Procesados {i} documentos... Relaciones latentes encontradas: {len(nuevas_relaciones)}")

    if nuevas_relaciones:
        # Inyectamos con peso inicial = 1 (Arista Ciega) para que luego el extractor semántico la evalúe
        cursor.executemany("""
            INSERT INTO relaciones_organicas (origen, destino, peso, ultima_actualizacion)
            VALUES (?, ?, 1.0, ?)
            ON CONFLICT(origen, destino) DO UPDATE SET 
            ultima_actualizacion = excluded.ultima_actualizacion,
            peso = 1.0
        """, nuevas_relaciones)
        conn.commit()
        print(f"\n[+] Éxito. Se inyectaron {len(nuevas_relaciones)} relaciones orgánicas realistas en la topología.")
    else:
        print("\n[*] No se encontraron relaciones cruzadas en el historial.")

    conn.close()

if __name__ == "__main__":
    mineria_entidades_retroactiva()