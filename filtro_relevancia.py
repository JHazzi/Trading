import sqlite3
import torch
from transformers import pipeline

DB_PATH = "data/market_data.db"
BATCH_SIZE = 16  # Ajustable según tu VRAM libre

# 1. Configuración de Aceleración de Hardware
device_id = 0 if torch.cuda.is_available() else -1
if device_id == 0:
    print(f"[*] GPU detectada para Zero-Shot: {torch.cuda.get_device_name(0)}")

# 2. Carga del Modelo Zero-Shot (BART Large MNLI)
print("[*] Cargando modelo semántico BART-Large-MNLI...")
clasificador = pipeline(
    "zero-shot-classification", 
    model="facebook/bart-large-mnli", 
    device=device_id
)

def procesar_relevancia():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buscamos noticias sin evaluar, o las que fueron evaluadas por el viejo sistema Regex (distintas de 1.0 que es la SEC pura)
    cursor.execute("""
        SELECT id, titulo, resumen 
        FROM noticias 
        WHERE importancia IS NULL OR importancia != 1.0
    """)
    filas = cursor.fetchall()
    
    if not filas:
        print("[!] No hay noticias pendientes de evaluar.")
        conn.close()
        return 0
        
    print(f"[*] Evaluando semántica profunda para {len(filas)} noticias...")
    
    actualizaciones = []
    
    # Procesamiento en Lotes (Batches) para saturar los Tensor Cores de la GPU
    for i in range(0, len(filas), BATCH_SIZE):
        batch = filas[i : i + BATCH_SIZE]
        ids = [f[0] for f in batch]
        
        # Fusionamos título y resumen (con un fallback seguro si resumen es None)
        textos = [f"{f[1]}. {f[2] if f[2] else ''}" for f in batch]
        
        try:
            # multi_label=True fuerza al modelo a devolver una probabilidad de 0 a 1 independiente para esta etiqueta
            resultados = clasificador(
                textos, 
                candidate_labels=["critical market moving corporate event"],
                multi_label=True
            )
            
            for idx, res in enumerate(resultados):
                # Extraemos el score matemático de la etiqueta
                score = round(res['scores'][0], 4)
                actualizaciones.append((score, ids[idx]))
                
        except Exception as e:
            print(f"[!] Error procesando batch de textos: {e}")
            continue
            
    # Actualización masiva en SQLite
    if actualizaciones:
        cursor.executemany("UPDATE noticias SET importancia = ? WHERE id = ?", actualizaciones)
        conn.commit()
        
    conn.close()
    return len(actualizaciones)

if __name__ == "__main__":
    procesadas = procesar_relevancia()
    print(f"[+] Relevancia asignada matemáticamente para {procesadas} noticias.")