/**
 * Módulo de Configuración (config.js)
 * Lee y escribe los ajustes globales del bot.
 */

const ConfigMotor = {
    cargarConfig: async function() {
        try {
            const config = await API.getConfig();
            
            // Poblar Intervalos
            document.getElementById('cfg-int-precios').value = config.intervalos_segundos.precios;
            document.getElementById('cfg-int-noticias').value = config.intervalos_segundos.noticias;
            document.getElementById('cfg-int-cerebro').value = config.intervalos_segundos.cerebro;
            
            // Poblar IA y Trading
            document.getElementById('cfg-ia-certeza').value = config.trading.certeza_minima_ia_pct;
            document.getElementById('cfg-ia-similitud').value = config.ia.umbral_similitud_eventos;
            document.getElementById('cfg-risk-pct').value = config.trading.riesgo_por_operacion_pct;

        } catch (error) {
            console.error("Error al cargar configuración:", error);
        }
    },

    guardarConfig: async function() {
        const btn = event.target;
        btn.innerText = "Guardando...";
        
        try {
            // Reconstruimos el objeto respetando la estructura de config.json
            const nuevaConfig = {
                intervalos_segundos: {
                    precios: parseInt(document.getElementById('cfg-int-precios').value),
                    noticias: parseInt(document.getElementById('cfg-int-noticias').value),
                    cerebro: parseInt(document.getElementById('cfg-int-cerebro').value),
                    macro: 86400 // Lo dejamos fijo por ahora
                },
                trading: {
                    riesgo_por_operacion_pct: parseFloat(document.getElementById('cfg-risk-pct').value),
                    horizonte_inversion_horas: 24,
                    certeza_minima_ia_pct: parseFloat(document.getElementById('cfg-ia-certeza').value)
                },
                ia: {
                    batch_size: 16,
                    umbral_similitud_eventos: parseFloat(document.getElementById('cfg-ia-similitud').value)
                }
            };

            await API.guardarConfig(nuevaConfig);
            
            // Feedback visual
            const msg = document.getElementById('cfg-msg');
            msg.style.display = 'inline';
            setTimeout(() => { msg.style.display = 'none'; }, 3000);

        } catch (error) {
            console.error("Error al guardar:", error);
            alert("No se pudo guardar la configuración.");
        } finally {
            btn.innerText = "Guardar Configuración";
        }
    }
};

window.ConfigMotor = ConfigMotor;