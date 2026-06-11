
import { groupDataByYearAndQuestion, extractQuestions, getAverage, extractYear, wrapTextByWords, createLineChart, setupPngDownload, setupPdfDownload } from '/static/js/utils.js';

document.addEventListener('DOMContentLoaded', function() {
    const apiUrlElement = document.getElementById('api-url');
    const container = document.getElementById('charts-container');
    const spinner = document.getElementById('loading-spinner');
    const rangeLabel = document.getElementById('range-label');
    const template = document.getElementById('chart-template');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');

    let allCharts = [];
    let processedSeries = [];
    let globalYears = [];

    if (!apiUrlElement || !container || !template) return;

    setupPdfDownload(downloadPdfBtn, 'charts-container', 'Report_Materia.pdf');

    fetch(apiUrlElement.value)
        .then(response => response.json())
        .then(data => {
            if (spinner) spinner.style.display = 'none';
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="col-12"><div class="alert alert-info shadow-sm text-center">Nessun report disponibile per questa materia.</div></div>';
                return;
            }
            processAndDrawCharts(data);
        })
        .catch(err => {
            if (spinner) spinner.style.display = 'none';
            console.error(err);
        });

    function processAndDrawCharts(datasets) {
        let yearsSet = new Set();
        datasets.forEach(ds => yearsSet.add(extractYear(ds)));
        globalYears = Array.from(yearsSet).sort();

        const groupedData = groupDataByYearAndQuestion(datasets);
        const questions = Array.from(extractQuestions(groupedData));

        container.innerHTML = '';

        questions.forEach((domanda, index) => {
            
            const freqData = globalYears.map(year => {
                let stats = getAverage(groupedData, year, domanda, 'Frequentanti');
                return stats ? { ...stats, x: year } : null;
            });
            
            const nonFreqData = globalYears.map(year => {
                let stats = getAverage(groupedData, year, domanda, 'Non Frequentanti');
                return stats ? { ...stats, x: year } : null;
            });

            processedSeries.push({ years: globalYears, freqData: freqData, nonFreqData: nonFreqData });

            const clone = template.content.cloneNode(true);
            clone.querySelector('.chart-title').textContent = ''; 
            
            const canvas = clone.querySelector('.chart-canvas');
            canvas.id = `chart-${index}`;
            const downloadPngBtn = clone.querySelector('.download-png-btn');
            container.appendChild(clone);

            const chartDatasets = [
                {
                    label: 'Frequentanti', data: freqData,
                    borderColor: '#0d6efd', backgroundColor: 'rgba(13, 110, 253, 0)',
                    borderWidth: 3, tension: 0.3, spanGaps: true,
                    pointBackgroundColor: '#ffffff', pointBorderColor: '#0d6efd', pointBorderWidth: 2, pointRadius: 5
                },
                {
                    label: 'Non Frequentanti', data: nonFreqData,
                    borderColor: '#dc3545', backgroundColor: 'rgba(220, 53, 69, 0)',
                    borderWidth: 3, tension: 0.3, spanGaps: true,
                    pointBackgroundColor: '#ffffff', pointBorderColor: '#dc3545', pointBorderWidth: 2, pointRadius: 5
                }
            ];

            // Generiamo il titolo per Chart.js spezzando la frase (max 10 parole per riga)
            const titleLines = wrapTextByWords(domanda, 15);

            // Passiamo il titolo a utils.js!
            const newChart = createLineChart(canvas.getContext('2d'), globalYears, chartDatasets, titleLines);
            setupPngDownload(downloadPngBtn, newChart, `grafico_domanda_${index + 1}.png`);

            allCharts.push(newChart);
        });

        initSlider(globalYears.length);
        updateAll(0, globalYears.length - 1);
    }

    function initSlider(totalYears) {
        if (!$("#slider-range").length) return;
        $("#slider-range").slider({
            range: true, min: 0, max: totalYears - 1, values: [0, totalYears - 1],
            slide: (event, ui) => updateAll(ui.values[0], ui.values[1])
        });
    }

    function updateAll(minIdx, maxIdx) {
        const sampleYears = globalYears.slice(minIdx, maxIdx + 1);
        if (rangeLabel && sampleYears.length > 0) rangeLabel.textContent = `${sampleYears[0]} — ${sampleYears[sampleYears.length - 1]}`;
        
        allCharts.forEach((chart, i) => {
            chart.data.labels = processedSeries[i].years.slice(minIdx, maxIdx + 1);
            chart.data.datasets[0].data = processedSeries[i].freqData.slice(minIdx, maxIdx + 1);
            chart.data.datasets[1].data = processedSeries[i].nonFreqData.slice(minIdx, maxIdx + 1);
            chart.update('none'); 
        });
    }
});
