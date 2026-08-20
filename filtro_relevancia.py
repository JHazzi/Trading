import sqlite3
import re

DB_PATH = "data/market_data.db"

# 1. Diccionarios Regex
# Criba rápida: Listicles, clickbait, análisis de baja calidad
BASURA_REGEX = re.compile(
    r"(?i)(\b\d+\s+stocks?\s+to\s+buy\b|reasons\s+why|things\s+to\s+know|what\s+to\s+watch|stock\s+advisor|zacks\s+rank|motley\s+fool|should\s+you\s+invest|is\s+it\s+too\s+late|dividend\s+yield|buy\s+alert)"
)

# Eventos estructurales: Tienen implicaciones directas en el valor
ALTO_IMPACTO_REGEX = re.compile(
    r"(?i)(acquire|acquisition|merger|buyout|earnings|guidance|sec\s+filing|lawsuit|sues|investigation|fda\s+approval|bankruptcy|spins\s+off|resigns|layoffs)"
)

def evaluar_relevancia_texto(titulo: str, resumen: str) -> float:
    """
    Asigna un valor continuo [0, 1] de importancia basado en el contenido.
    """
    texto_completo = f"{titulo} {resumen}"
    
    # Si contiene lenguaje amarillista o de listado, importancia nula
    if BASURA_REGEX.search(texto_completo):
        return 0.0
        
    # Si contiene eventos corporativos reales, alta importancia
    if ALTO_IMPACTO_REGEX.search(texto_completo):
        return 0.9
        
    # Si no cae en los extremos, es una noticia normal de ecosistema (Ruido de fondo válido)
    return 0.5

def procesar_relevancia() -> int:
    """
    Busca noticias sin puntuar y actualiza su nivel de importancia.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buscar solo noticias que no han sido pasadas por este filtro
    cursor.execute("SELECT id, titulo, resumen FROM noticias WHERE importancia IS NULL")
    filas = cursor.fetchall()
    
    if not filas:
        conn.close()
        return 0
        
    actualizaciones = []
    for id_noticia, titulo, resumen in filas:
        # Prevención de Nulos por si el scraper falló
        res_limpio = resumen if resumen else "" 
        importancia = evaluar_relevancia_texto(titulo, res_limpio)
        actualizaciones.append((importancia, id_noticia))
        
    cursor.executemany("UPDATE noticias SET importancia = ? WHERE id = ?", actualizaciones)
    conn.commit()
    conn.close()
    
    return len(actualizaciones)

if __name__ == "__main__":
    procesadas = procesar_relevancia()
    print(f"[+] Relevancia evaluada para {procesadas} noticias en la base de datos.")