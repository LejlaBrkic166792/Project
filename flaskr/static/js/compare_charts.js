// ==========================================
// FILE: static/js/compare_charts.js
// ==========================================

import { groupDataByYearAndQuestion, extractQuestions, getAverage, extractYear, wrapTextByWords, createLineChart, setupPngDownload, setupPdfDownload } from '/static/js/utils.js';

document.addEventListener("DOMContentLoaded", function() {
    const btnCompare = document.getElementById("btn-compare");
    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    const select1 = document.getElementById("subject1-select");
    const select2 = document.getElementById("subject2-select");
    const errorMsg = document.getElementById("compare-error-message");
    const spinner = document.getElementById("loading-spinner");
    const container = document.getElementById("compare-charts-container");

    if(!btnCompare) return;

    setupPdfDownload(downloadPdfBtn, 'compare-charts-container', 'Confronto_Materie.pdf');

    btnCompare.addEventListener("click", function() {
        const id1 = select1.value;
        const id2 = select2.value;

        if (!id1 || !id2) return showError("Seleziona entrambe le materie.");
        if (id1 === id2) return showError("Scegli due materie diverse.");

        errorMsg.classList.add("d-none");
        downloadPdfBtn.classList.add("d-none"); 
        container.innerHTML = "";
        spinner.classList.remove("d-none");

        fetch(`/api/compare/${id1}/${id2}`)
            .then(response => response.json())
            .then(data => {
                spinner.classList.add("d-none");
                if (data.error) showError(data.error);
                else drawComparisonCharts(data.subject1, data.subject2);
            })
            .catch(err => {
                spinner.classList.add("d-none");
                showError("Errore durante il caricamento dei report.");
            });
    });

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.classList.remove("d-none");
    }

    function drawComparisonCharts(sub1, sub2) {
        let allYears = new Set();
        sub1.datasets.forEach(ds => allYears.add(extractYear(ds)));
        sub2.datasets.forEach(ds => allYears.add(extractYear(ds)));
        const sortedYears = Array.from(allYears).sort();

        const dataSub1 = groupDataByYearAndQuestion(sub1.datasets);
        const dataSub2 = groupDataByYearAndQuestion(sub2.datasets);

        let allQuestions = new Set();
        extractQuestions(dataSub1).forEach(q => allQuestions.add(q));
        extractQuestions(dataSub2).forEach(q => allQuestions.add(q));

        if (allQuestions.size === 0) return showError("Nessun dato valido trovato nei CSV.");

        let chartsDrawn = 0;

        Array.from(allQuestions).forEach((domanda, index) => {
            let chartDatasets = [];

            const config = [
                { name: sub1.name, data: dataSub1, tipo: 'Frequentanti', color: '#0d6efd', dash: [] }, 
                { name: sub1.name, data: dataSub1, tipo: 'Non Frequentanti', color: '#0d6efd', dash: [5, 5] }, 
                { name: sub2.name, data: dataSub2, tipo: 'Frequentanti', color: '#dc3545', dash: [] }, 
                { name: sub2.name, data: dataSub2, tipo: 'Non Frequentanti', color: '#dc3545', dash: [5, 5] } 
            ];

            config.forEach(cfg => {
                const hasData = sortedYears.some(year => getAverage(cfg.data, year, domanda, cfg.tipo) !== null);
                if (hasData) {
                    chartDatasets.push({
                        label: `${cfg.name} (${cfg.tipo})`,
                        data: sortedYears.map(year => getAverage(cfg.data, year, domanda, cfg.tipo)),
                        borderColor: cfg.color, borderDash: cfg.dash, backgroundColor: 'transparent',
                        borderWidth: 3, tension: 0.3, spanGaps: true,
                        pointBackgroundColor: '#ffffff', pointBorderColor: cfg.color, pointBorderWidth: 2, pointRadius: 5
                    });
                }
            });

            if (chartDatasets.length === 0) return;

            const template = document.getElementById("compare-chart-template");
            const clone = template.content.cloneNode(true);
            
            // Lasciamo vuoto l'h5 HTML per non avere il doppio titolo
            clone.querySelector(".chart-title").textContent = ''; 
            
            const canvas = clone.querySelector(".chart-canvas");
            canvas.id = `compare-chart-${index}`;
            const downloadPngBtn = clone.querySelector('.download-png-btn');
            
            container.appendChild(clone);

            // Generiamo il titolo per Chart.js
            const titleLines = wrapTextByWords(domanda, 15);

            // Passiamo il titolo a utils.js!
            const newChart = createLineChart(canvas.getContext('2d'), sortedYears, chartDatasets, titleLines);
            setupPngDownload(downloadPngBtn, newChart, `Confronto_Domanda_${index + 1}.png`);

            chartsDrawn++;
        });

        if (chartsDrawn > 0) downloadPdfBtn.classList.remove("d-none");
    }
});