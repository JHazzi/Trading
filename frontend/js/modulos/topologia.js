/**
 * Módulo de Topología (topologia.js)
 * Renderiza el Grafo Semántico corporativo usando Vis.js
 */

const Topologia = {
    networkInstancia: null,

    renderizar: async function() {
        const contenedor = document.getElementById('chart-network');
        if (!contenedor) return;

        contenedor.innerHTML = '<div style="color: var(--text-muted); padding: 20px; text-align: center;">Calculando topología neuronal...</div>';

        try {
            // Llamamos a api.py -> /api/grafo
            const data = await API.getTopologia(); 
            contenedor.innerHTML = ''; // Limpiamos el mensaje de carga

            // Configuramos Vis.js para modo oscuro y fluidez institucional
            const options = {
                nodes: {
                    shape: 'dot',
                    size: 16,
                    font: { 
                        color: '#E2E8F0', 
                        size: 12, 
                        face: 'Inter',
                        strokeWidth: 2,
                        strokeColor: '#0B0E14' // Contorno oscuro para que el texto resalte
                    },
                    borderWidth: 2,
                    color: {
                        background: '#1E293B',
                        border: '#3B82F6',
                        highlight: { background: '#3B82F6', border: '#E2E8F0' }
                    }
                },
                edges: {
                    width: 1.5,
                    smooth: { type: 'continuous' },
                    color: { inherit: false } // Usa el color rojo/verde que manda la API
                },
                physics: {
                    forceAtlas2Based: { 
                        gravitationalConstant: -70, 
                        centralGravity: 0.01, 
                        springLength: 120, 
                        springConstant: 0.08 
                    },
                    maxVelocity: 50,
                    solver: 'forceAtlas2Based',
                    timestep: 0.35,
                    stabilization: { iterations: 150 }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200,
                    zoomView: true
                }
            };

            // Inyectamos el lienzo interactivo
            this.networkInstancia = new vis.Network(contenedor, data, options);

        } catch (error) {
            console.error("Error al graficar topología:", error);
            contenedor.innerHTML = '<div style="color: var(--bearish); padding: 20px; text-align: center;">Error al cargar el grafo semántico.</div>';
        }
    }
};

window.Topologia = Topologia;