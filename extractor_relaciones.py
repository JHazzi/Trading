import sqlite3
import torch
from transformers import pipeline

DB_PATH = "data/market_data.db"
BATCH_SIZE = 16

# Categorías semánticas y sus pesos matemáticos (W) para el Grafo
ETIQUETAS_RELACION = {
    "merger, acquisition, or buyout": 0.9,
    "partnership, collaboration, or supply agreement": 0.7,
    "generic mention or industry trend": 0.1,  # Ruido de fondo
    "market competition or rivalry": -0.4,
    "lawsuit, legal dispute, or patent conflict": -0.8
}

def inicializar_modelo():
    device_id = 0 if torch.cuda.is_available() else -1
    print("[*] Cargando modelo de Extracción de Relaciones (BART-Large-MNLI)...")
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device_id)

def extraer_aristas_semanticas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Traemos las relaciones orgánicas que aún tienen el peso "tonto" por defecto (peso = 1 o enteros positivos)
    # y cruzamos con la tabla de noticias para obtener el texto del evento que las unió.
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

    print(f"[*] Analizando la semántica de {len(relaciones)} conexiones empresariales...")
    
    clasificador = inicializar_modelo()
    candidatos = list(ETIQUETAS_RELACION.keys())
    actualizaciones = []
    
    # Procesamiento en lotes para la GPU
    for i in range(0, len(relaciones), BATCH_SIZE):
        batch = relaciones[i : i + BATCH_SIZE]
        
        # Le damos al modelo el contexto completo: "La empresa A y la empresa B se mencionan aquí: [Texto]"
        textos = []
        for origen, destino, titulo, resumen in batch:
            texto_base = f"{titulo}. {resumen if resumen else ''}"
            prompt = f"The relationship between {origen} and {destino} in this text is: {texto_base}"
            textos.append(prompt)
            
        try:
            resultados = clasificador(textos, candidate_labels=candidatos, multi_label=False)
            
            for idx, res in enumerate(resultados):
                # La etiqueta con mayor probabilidad gana
                etiqueta_ganadora = res['labels'][0]
                peso_semantico = ETIQUETAS_RELACION[etiqueta_ganadora]
                
                origen = batch[idx][0]
                destino = batch[idx][1]
                
                actualizaciones.append((peso_semantico, origen, destino))
                
        except Exception as e:
            print(f"[!] Error procesando batch: {e}")
            continue

    # 2. Actualizar el Grafo con los pesos matemáticos reales
    if actualizaciones:
        cursor.executemany("""
            UPDATE relaciones_organicas 
            SET peso = ? 
            WHERE origen = ? AND destino = ?
        """, actualizaciones)
        conn.commit()
        print(f"[+] Grafo actualizado: {len(actualizaciones)} aristas convertidas a vectores semánticos.")

    conn.close()

if __name__ == "__main__":
    extraer_aristas_semanticas()