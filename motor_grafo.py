import sqlite3
import networkx as nx

DB_PATH = "data/market_data.db"

def cargar_grafo_mercado() -> nx.DiGraph:
    """Construye el grafo dirigido en memoria leyendo SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    G = nx.DiGraph()
    
    # Cargar Nodos (El universo de activos)
    cursor.execute("SELECT ticker FROM universo_tickers WHERE activo = 1")
    nodos = [fila[0] for fila in cursor.fetchall()]
    G.add_nodes_from(nodos)
    
    # Cargar Aristas (Relaciones con pesos) - CORREGIDO
    cursor.execute("SELECT origen, destino, peso FROM relaciones_organicas")
    aristas = cursor.fetchall()
    for origen, destino, peso in aristas:
        G.add_edge(origen, destino, weight=peso)
        
    conn.close()
    return G

def calcular_shock_contagio(ticker_origen: str, sentimiento_inicial: float, G: nx.DiGraph) -> dict:
    """
    Propaga el sentimiento a través de los nodos vecinos de profundidad 1.
    Retorna un diccionario con el impacto colateral en otros tickers.
    """
    impactos = {}
    
    # Verificamos si el ticker está en nuestro grafo
    if ticker_origen not in G:
        return impactos
        
    # Iteramos sobre los sucesores (quiénes son afectados por el origen)
    for vecino in G.successors(ticker_origen):
        peso_relacion = G[ticker_origen][vecino]['weight']
        
        # Fórmula de transferencia de sentimiento
        sentimiento_transferido = sentimiento_inicial * peso_relacion
        
        # Guardamos el impacto si es estadísticamente relevante (filtro de ruido)
        if abs(sentimiento_transferido) > 0.05:
            impactos[vecino] = round(sentimiento_transferido, 4)
            
    return impactos

if __name__ == "__main__":
    # Prueba de concepto aislada
    grafo = cargar_grafo_mercado()
    print("[*] Grafo cargado en memoria.")
    print(f"Nodos: {grafo.number_of_nodes()}")
    print(f"Aristas: {grafo.number_of_edges()}")
    
    # Simulamos una noticia de Grado 1 sobre NVIDIA muy positiva
    ticker_noticia = "NVDA"
    sentimiento_noticia = 0.85 
    
    print(f"\n[!] SHOCK INICIAL: Noticia en {ticker_noticia} con fuerza de {sentimiento_noticia}")
    
    contagios = calcular_shock_contagio(ticker_noticia, sentimiento_noticia, grafo)
    
    if contagios:
        print("\n[*] Propagación calculada:")
        for afectado, impacto in contagios.items():
            direccion = "Positivo" if impacto > 0 else "Negativo"
            print(f"    -> {afectado}: Recibe un impacto {direccion} de {impacto}")
    else:
        print("\n[*] Sin contagios calculados (Grafo sin aristas para este nodo).")