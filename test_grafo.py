import networkx as nx
import matplotlib.pyplot as plt

# 1. Instanciar un grafo dirigido (las relaciones tienen un sentido/flecha)
G = nx.DiGraph()

# 2. Agregar Nodos (Entidades del mercado)
nodos = ["Apple (AAPL)", "TSMC (Proveedor)", "Sector Tecnológico", "Noticia: Escasez de Chips"]
G.add_nodes_from(nodos)

# 3. Agregar Aristas (Relaciones con un "peso" o tipo de impacto)
G.add_edge("Noticia: Escasez de Chips", "TSMC (Proveedor)", impacto="Directo Negativo")
G.add_edge("TSMC (Proveedor)", "Apple (AAPL)", impacto="Cadena de Suministro")
G.add_edge("Apple (AAPL)", "Sector Tecnológico", impacto="Correlación de Indice")

# 4. Dibujar el Grafo
plt.figure(figsize=(10, 6))

# Calcular la posición de los nodos para que se vea ordenado
pos = nx.spring_layout(G, seed=42) 

# Dibujar nodos y etiquetas
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=3000, font_size=10, font_weight='bold', arrows=True)

# Dibujar las etiquetas de las relaciones (aristas)
edge_labels = nx.get_edge_attributes(G, 'impacto')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

plt.title("Prueba de Grafo de Conocimiento del Mercado")

# Guardar como imagen (en WSL es mejor guardar en archivo que intentar abrir ventanas)
plt.savefig("grafo_prueba.png")
print("Grafo generado y guardado como 'grafo_prueba.png'")