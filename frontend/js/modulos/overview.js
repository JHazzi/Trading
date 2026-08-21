/**
 * Módulo Overview (overview.js)
 * Auditoría Predictiva: Rendimiento Esperado vs Real por Acción
 */

const Overview = {
    chartInstancia: null,

    renderizar: async function() {
        const contenedor = document.getElementById('chart-equity');
        const tickerSeleccionado = document.getElementById('overview-ticker').value;
        if (!contenedor) return;

        if (!this.chartInstancia) {
            this.chartInstancia = echarts.init(contenedor);
            window.addEventListener('resize', () => this.chartInstancia.resize());
        }

        this.chartInstancia.showLoading({ color: '#3B82F6', maskColor: 'rgba(11, 14, 20, 0.8)' });

        try {
            const operaciones = await API.fetchJSON("/operaciones");
            
            // Poblar el selector solo con los tickers que la IA ya operó
            this.poblarSelector(operaciones, tickerSeleccionado);

            // Filtrar por acción si el usuario seleccionó una
            const opsFiltradas = tickerSeleccionado === 'ALL' 
                ? operaciones 
                : operaciones.filter(op => op.ticker === tickerSeleccionado);

            // Separar solo las operaciones que ya cerraron (maduras)
            const maduras = opsFiltradas.filter(op => op.rendimiento_real_pct !== null);

            if (maduras.length === 0) {
                this.dibujarGraficoVacio();
                return;
            }

            const fechas = [];
            const curvaEsperada = [];
            const curvaReal = [];
            let capEsperado = 100.0;
            let capReal = 100.0;

            // Invertimos porque vienen DESC desde la API
            [...maduras].reverse().forEach(op => {
                // Formateamos fecha y hora (ej: 08-20 14:30)
                const f = new Date(op.fecha_senal);
                fechas.push(`${f.getMonth()+1}/${f.getDate()} ${f.getHours()}:${f.getMinutes().toString().padStart(2, '0')}`);
                
                capEsperado += op.rendimiento_esperado_pct;
                capReal += op.rendimiento_real_pct;
                
                curvaEsperada.push(capEsperado.toFixed(2));
                curvaReal.push(capReal.toFixed(2));
            });

            const option = {
                backgroundColor: 'transparent',
                tooltip: { trigger: 'axis' },
                legend: { data: ['IA (Esperado)', 'Mercado (Real)'], textStyle: { color: '#E2E8F0' } },
                grid: { left: '5%', right: '5%', bottom: '10%', top: '15%' },
                xAxis: { type: 'category', data: fechas, axisLine: { lineStyle: { color: '#2B303B' } }, axisLabel: { color: '#64748B' } },
                yAxis: { type: 'value', min: 'dataMin', axisLine: { lineStyle: { color: '#2B303B' } }, splitLine: { lineStyle: { color: '#151922' } }, axisLabel: { formatter: '{value}%', color: '#64748B' } },
                series: [
                    {
                        name: 'IA (Esperado)',
                        type: 'line',
                        data: curvaEsperada,
                        lineStyle: { color: '#64748B', width: 2, type: 'dashed' }, // Línea punteada gris
                        symbol: 'none'
                    },
                    {
                        name: 'Mercado (Real)',
                        type: 'line',
                        data: curvaReal,
                        smooth: true,
                        lineStyle: { color: '#3B82F6', width: 3 }, // Línea azul sólida
                        symbol: 'none',
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
                                { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
                            ])
                        }
                    }
                ]
            };

            this.chartInstancia.setOption(option);
        } catch (error) {
            console.error("Error al graficar Auditoría:", error);
            this.chartInstancia.clear();
        } finally {
            this.chartInstancia.hideLoading();
        }
    },

    poblarSelector: function(operaciones, actual) {
        const select = document.getElementById('overview-ticker');
        const tickersUnicos = [...new Set(operaciones.map(op => op.ticker))].sort();
        
        select.innerHTML = '<option value="ALL">Portafolio Global</option>';
        tickersUnicos.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            if (t === actual) opt.selected = true;
            select.appendChild(opt);
        });
    },

    dibujarGraficoVacio: function() {
        this.chartInstancia.setOption({
            backgroundColor: 'transparent',
            title: { text: 'Esperando que las operaciones alcancen su horizonte de maduración...', left: 'center', top: 'center', textStyle: { color: '#64748B', fontSize: 14, fontWeight: 'normal' } }
        }, true);
    }
};

window.Overview = Overview;