import sqlite3
import torch
import json
from transformers import pipeline

DB_PATH = "data/market_data.db"
CONFIG_PATH = "config.json"

def cargar_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def inicializar_modelo():
    device_id = 0 if torch.cuda.is_available() else -1
    print(f"[*] Aceleración por hardware: {'Activada (GPU)' if device_id == 0 else 'Desactivada (CPU)'}")
    print("[*] Cargando modelo de Extracción de Relaciones (BART-Large-MNLI)...")
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device_id)

def extraer_aristas_semanticas():
    # 1. Leemos dinámicamente la configuración
    config = cargar_config()
    batch_size = config["ia"]["batch_size"]
    etiquetas_relacion = config["taxonomia_relaciones"] # Cargamos la taxonomía del JSON

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT r.origen, r.destino, n.titulo, n.resumen 
        FROM relaciones_organicas r
        JOIN noticias n ON n.ticker = r.origen AND n.timestamp = r.ultima_actualizacion
        WHERE r.peso >= 1.0 
    """
    cursor.execute(query)
    relaciones = cursor.fetchall()
    
    if not relaciones:
        print("[!] No hay aristas ciegas pendientes de evaluar en el Grafo.")
        conn.close()
        return

    total_relaciones = len(relaciones)
    print(f"[*] Analizando la semántica de {total_relaciones} conexiones con Lotes de {batch_size}...")
    
    clasificador = inicializar_modelo()
    candidatos = list(etiquetas_relacion.keys()) # Extraemos solo los nombres para la IA
    actualizaciones = []
    
    for i in range(0, total_relaciones, batch_size):
        batch = relaciones[i : i + batch_size]
        
        textos = []
        for origen, destino, titulo, resumen in batch:
            texto_base = f"{titulo}. {resumen if resumen else ''}"
            prompt = f"The relationship between {origen} and {destino} in this text is: {texto_base}"
            textos.append(prompt)
            
        try:
            resultados = clasificador(textos, candidate_labels=candidatos, multi_label=False)
            
            for idx, res in enumerate(resultados):
                etiqueta_ganadora = res['labels'][0]
                # Buscamos el peso matemático asociado a la etiqueta ganadora
                peso_semantico = etiquetas_relacion[etiqueta_ganadora] 
                
                origen = batch[idx][0]
                destino = batch[idx][1]
                
                actualizaciones.append((peso_semantico, origen, destino))
                
        except Exception as e:
            print(f"  [!] Error procesando batch: {e}")
            continue

        # --- FEEDBACK VISUAL Y GUARDADO PARCIAL ---
        if i % (batch_size * 20) == 0 and i > 0:
            porcentaje = (i / total_relaciones) * 100
            print(f"  -> Procesadas {i}/{total_relaciones} conexiones ({porcentaje:.1f}%)")
            
            cursor.executemany("""
                UPDATE relaciones_organicas 
                SET peso = ? 
                WHERE origen = ? AND destino = ?
            """, actualizaciones)
            conn.commit()
            actualizaciones.clear() 

    # Guardado del remanente final
    if actualizaciones:
        cursor.executemany("""
            UPDATE relaciones_organicas 
            SET peso = ? 
            WHERE origen = ? AND destino = ?
        """, actualizaciones)
        conn.commit()
        
    print(f"\n[+] Grafo actualizado exitosamente. Topología semántica lista.")
    conn.close()

if __name__ == "__main__":
    extraer_aristas_semanticas()