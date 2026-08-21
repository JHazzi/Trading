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
                    size: 14,
                    font: { 
                        color: '#E2E8F0', 
                        size: 11, 
                        face: 'Inter',
                        strokeWidth: 3,
                        strokeColor: '#0B0E14' 
                    },
                    borderWidth: 2,
                    color: {
                        background: '#1E293B',
                        border: '#3B82F6',
                        highlight: { background: '#3B82F6', border: '#E2E8F0' }
                    }
                },
                edges: {
                    width: 1.2,
                    smooth: { type: 'continuous' },
                    // LA CLAVE: Opacidad al 40% para que no colapsen visualmente
                    color: { inherit: false, opacity: 0.4 } 
                },
                physics: {
                    forceAtlas2Based: { 
                        gravitationalConstant: -150, // Más repulsión para separar el cúmulo
                        centralGravity: 0.005, 
                        springLength: 200, // Cuerdas más largas entre empresas
                        springConstant: 0.05 
                    },
                    maxVelocity: 40,
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
            this.networkInstancia.once("stabilizationIterationsDone", () => {
                this.networkInstancia.setOptions({ physics: false });
            });

        } catch (error) {
            console.error("Error al graficar topología:", error);
            contenedor.innerHTML = '<div style="color: var(--bearish); padding: 20px; text-align: center;">Error al cargar el grafo semántico.</div>';
        }
    }
};

window.Topologia = Topologia;