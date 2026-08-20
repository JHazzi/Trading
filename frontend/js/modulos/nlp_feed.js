/**
 * Módulo Laboratorio NLP (nlp_feed.js)
 * Renderiza la terminal de noticias y el análisis semántico.
 */

const NLPFeed = {
    renderizar: async function() {
        const tbody = document.getElementById('tabla-noticias');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando flujo de eventos...</td></tr>';
        
        try {
            // Pedimos las últimas 50 noticias a la API
            const noticias = await API.getNoticias(50);
            tbody.innerHTML = '';
            
            noticias.forEach(n => {
                const tr = document.createElement('tr');
                
                // Formateo de datos
                const fecha = new Date(n.timestamp).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' });
                const sentimientoClass = n.sentimiento > 0 ? 'text-bullish' : (n.sentimiento < 0 ? 'text-bearish' : '');
                const sentimientoValor = n.sentimiento !== null ? parseFloat(n.sentimiento).toFixed(2) : 'N/A';
                const importancia = n.importancia !== null ? (n.importancia * 100).toFixed(0) + '%' : '--';
                const resumenCorto = n.resumen ? n.resumen.substring(0, 110) + '...' : 'Sin resumen extraído.';
                
                tr.innerHTML = `
                    <td style="white-space:nowrap; color:var(--text-muted);">${fecha}</td>
                    <td><strong>${n.ticker}</strong></td>
                    <td>
                        <div style="font-weight:600; margin-bottom:4px; color:var(--text-main);">${n.titulo}</div>
                        <div style="color:var(--text-muted); font-size:11px; line-height:1.4;">${resumenCorto}</div>
                    </td>
                    <td class="${sentimientoClass}" style="font-weight:600;">${sentimientoValor}</td>
                    <td>${importancia}</td>
                `;
                tbody.appendChild(tr);
            });
            
        } catch(error) {
            console.error("Error cargando noticias:", error);
            tbody.innerHTML = `<tr><td colspan="5" class="text-bearish" style="text-align:center;">Error al conectar con la base de datos.</td></tr>`;
        }
    }
};

window.NLPFeed = NLPFeed;