document.addEventListener('DOMContentLoaded', function() {
    const apiUrlElement = document.getElementById('api-url');
    const container = document.getElementById('charts-container');
    const spinner = document.getElementById('loading-spinner');
    const rangeLabel = document.getElementById('range-label');
    const template = document.getElementById('chart-template');

    let allCharts = [];
    let processedData = [];

    if (!apiUrlElement || !container || !template) return;

    function cleanValue(val) {
        if (typeof val === 'string') {
            return parseFloat(val.replace(',', '.').replace('%', '').trim()) || 0;
        }
        return val || 0;
    }

    fetch(apiUrlElement.value)
        .then(response => response.json())
        .then(data => {
            if (spinner) spinner.style.display = 'none';
            if (!data || data.length === 0) return;

            const numeroDomande = data[0].data_json.length;

            for (let i = 0; i < numeroDomande; i++) {
                let serieStorica = data.map(d => {
                    const riga = d.data_json[i];
                    const v1 = cleanValue(riga["Decisamente No"] || 0);
                    const v2 = cleanValue(riga["Più No che Sì"] || 0);
                    const v3 = cleanValue(riga["Più Sì che No"] || 0);
                    const v4 = cleanValue(riga["Decisamente Sì"] || 0);
                    
                    const totale = v1 + v2 + v3 + v4;
                    const media = totale > 0 ? ((v1*1 + v2*2 + v3*3 + v4*4) / totale) : 0;

                    return {
                        anno: d.anno !== 'N/D' ? d.anno : d.filename.match(/\d{4}[\/_-]\d{2,4}/)?.[0] || d.filename,
                        media: media.toFixed(2),
                        testo: riga["Domanda"]
                    };
                });
                processedData.push(serieStorica);
            }

            initCharts(); 
            initSlider(data.length);
            updateAll(0, data.length - 1);
        });

    function initCharts() {
        // Puliamo il contenitore (rimuove lo spinner)
        container.innerHTML = ''; 

        processedData.forEach((serie, index) => {
            const clone = template.content.cloneNode(true);
            
            clone.querySelector('.chart-title').textContent = serie[0].testo;
            
            const canvas = clone.querySelector('.chart-canvas');
            canvas.id = `chart-${index}`;

            container.appendChild(clone);

            const ctx = canvas.getContext('2d');
            const newChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: serie.map(s => s.anno),
                    datasets: [{
                        label: 'Media Punteggio',
                        data: serie.map(s => s.media),
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.05)',
                        borderWidth: 3,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { 
                            min: 1, 
                            max: 4, 
                            ticks: { stepSize: 1 },
                            title: { display: true, text: 'Punteggio (1-4)' }
                        }
                    }
                }
            });
            allCharts.push(newChart);
        });
    }

    function initSlider(totalFiles) {
        $("#slider-range").slider({
            range: true,
            min: 0,
            max: totalFiles - 1,
            values: [0, totalFiles - 1],
            slide: function(event, ui) {
                updateAll(ui.values[0], ui.values[1]);
            }
        });
    }

    function updateAll(minIdx, maxIdx) {
        const sampleSerie = processedData[0].slice(minIdx, maxIdx + 1);
        if (rangeLabel && sampleSerie.length > 0) {
            rangeLabel.textContent = `${sampleSerie[0].anno} — ${sampleSerie[sampleSerie.length - 1].anno}`;
        }

        allCharts.forEach((chart, i) => {
            const dataFetta = processedData[i].slice(minIdx, maxIdx + 1);
            chart.data.labels = dataFetta.map(s => s.anno);
            chart.data.datasets[0].data = dataFetta.map(s => s.media);
            chart.update('none'); 
        });
    }
});