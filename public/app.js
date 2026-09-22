// Client-side JavaScript for GNN Molecular Property Prediction Web App

const TOX21_TASKS = [
    'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase',
    'NR-ER', 'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE',
    'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53'
];

let selectedArch = 'gcn';
let currentSmiles = 'CC(=O)OC1=CC=CC=C1C(=O)O';

document.addEventListener('DOMContentLoaded', () => {
    initTaskSelect();
    initArchButtons();
    loadPresets();
    
    document.getElementById('btn-predict').addEventListener('click', runPrediction);
    document.getElementById('btn-check-interaction').addEventListener('click', runInteractionPrediction);
    document.getElementById('btn-resolve-name').addEventListener('click', resolveCompoundName);
    document.getElementById('task-select').addEventListener('change', runPrediction);
    document.getElementById('smiles-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runPrediction();
    });

    // Run initial prediction for default Aspirin molecule
    runPrediction();
});

async function resolveCompoundName() {
    const nameInput = document.getElementById('compound-name-input');
    const status = document.getElementById('name-resolve-status');
    const btn = document.getElementById('btn-resolve-name');
    const name = nameInput.value.trim();

    if (!name) {
        status.textContent = 'Enter a chemical name first.';
        status.className = 'name-resolve-status error';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Resolving...';
    status.textContent = '';
    status.className = 'name-resolve-status';

    try {
        const res = await fetch('/api/name-to-smiles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        const data = await res.json();

        if (!res.ok) {
            status.textContent = data.error || 'Chemical name lookup failed.';
            status.className = 'name-resolve-status error';
            return;
        }

        document.getElementById('smiles-input').value = data.smiles;
        status.textContent = `Resolved to: ${data.smiles}`;
        status.className = 'name-resolve-status success';
        await runPrediction();
    } catch (err) {
        console.error('Name resolution error:', err);
        status.textContent = 'Failed to connect to backend server.';
        status.className = 'name-resolve-status error';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Resolve to SMILES';
    }
}

function initTaskSelect() {
    const select = document.getElementById('task-select');
    select.innerHTML = '';
    TOX21_TASKS.forEach((task, idx) => {
        const option = document.createElement('option');
        option.value = idx;
        option.textContent = `${idx + 1}. ${task}`;
        select.appendChild(option);
    });
}

function initArchButtons() {
    const buttons = document.querySelectorAll('.arch-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedArch = btn.dataset.arch;
            runPrediction();
        });
    });
}

async function loadPresets() {
    try {
        const res = await fetch('/api/presets');
        const data = await res.json();
        const container = document.getElementById('preset-chips');
        container.innerHTML = '';

        data.presets.forEach(p => {
            const chip = document.createElement('button');
            chip.className = 'chip';
            chip.textContent = p.name;
            chip.addEventListener('click', () => {
                document.getElementById('smiles-input').value = p.smiles;
                runPrediction();
            });
            container.appendChild(chip);
        });
    } catch (err) {
        console.error('Error loading presets:', err);
    }
}

async function runPrediction() {
    const smiles = document.getElementById('smiles-input').value.trim();
    const taskIdx = document.getElementById('task-select').value;
    const btn = document.getElementById('btn-predict');
    
    if (!smiles) return;

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                smiles: smiles,
                arch: selectedArch,
                task_idx: parseInt(taskIdx)
            })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.error || 'Prediction failed');
            return;
        }

        currentSmiles = smiles;
        updateUI(data);

    } catch (err) {
        console.error('Prediction error:', err);
        alert('Failed to connect to backend server.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play"></i> Run GNN';
    }
}

async function runInteractionPrediction() {
    const nameA = document.getElementById('ddi-name-a').value.trim();
    const nameB = document.getElementById('ddi-name-b').value.trim();
    const arch = document.getElementById('ddi-arch-select').value;
    const btn = document.getElementById('btn-check-interaction');
    const status = document.getElementById('ddi-status');
    const result = document.getElementById('ddi-result');

    result.hidden = true;
    result.innerHTML = '';

    if (!nameA || !nameB) {
        status.textContent = 'Enter both drug names before checking the interaction.';
        status.className = 'ddi-status error';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';
    status.textContent = '';
    status.className = 'ddi-status';

    try {
        const res = await fetch('/api/predict-interaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name_a: nameA, name_b: nameB, arch: arch })
        });
        const data = await res.json();

        if (!res.ok) {
            status.textContent = data.error || 'Interaction prediction failed.';
            status.className = 'ddi-status error';
            return;
        }

        const severity = data.predicted_severity;
        const severityClass = severity.toLowerCase();
        const probabilityRows = Object.entries(data.probabilities).map(([label, probability]) => {
            const percent = (probability * 100).toFixed(1);
            return `
                <div class="ddi-probability-row">
                    <div class="ddi-probability-label"><span>${label}</span><strong>${percent}%</strong></div>
                    <div class="prob-meter"><div class="prob-fill ddi-fill-${label.toLowerCase()}" style="width: ${percent}%;"></div></div>
                </div>`;
        }).join('');

        result.innerHTML = `
            <div class="ddi-result-summary ${severityClass}">
                <span class="ddi-result-label">Predicted severity</span>
                <strong>${severity}</strong>
            </div>
            <div class="ddi-probabilities">
                <h3>Class probabilities</h3>
                ${probabilityRows}
            </div>
            <div class="ddi-smiles">
                <div><span>${data.name_a}</span><code>${data.smiles_a}</code></div>
                <div><span>${data.name_b}</span><code>${data.smiles_b}</code></div>
            </div>`;
        result.hidden = false;
        loadInteractionSummary(nameA, nameB);
    } catch (err) {
        console.error('DDI prediction error:', err);
        status.textContent = 'Failed to connect to backend server.';
        status.className = 'ddi-status error';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Check Interaction';
    }
}

async function loadInteractionSummary(nameA, nameB) {
    const summary = document.getElementById('ddi-summary');
    summary.hidden = false;
    summary.innerHTML = '<span class="ddi-summary-loading"><i class="fa-solid fa-spinner fa-spin"></i> Loading DDInter summary...</span>';

    try {
        const res = await fetch('/api/interaction-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name_a: nameA, name_b: nameB })
        });
        const data = await res.json();

        if (!res.ok) {
            summary.innerHTML = `<p class="ddi-summary-muted">${data.error || 'DDInter summary unavailable.'}</p>`;
            return;
        }

        if (!data.available) {
            summary.innerHTML = `<p class="ddi-summary-muted">${data.reason || 'No detailed mechanism summary available for this pair.'}</p>`;
            return;
        }

        const categoryBadges = (data.categories || [])
            .map(category => `<span class="ddi-category-pill">${category}</span>`)
            .join('');
        summary.innerHTML = `
            <h3><i class="fa-solid fa-circle-info"></i> DDInter interaction summary</h3>
            <p class="ddi-summary-text">${data.summary}</p>
            <div class="ddi-category-list">${categoryBadges}</div>
            <p class="ddi-attribution">Source: <a href="${data.source_url}" target="_blank" rel="noopener noreferrer">${data.source} (${data.license})</a></p>`;
    } catch (err) {
        console.error('DDInter summary error:', err);
        summary.innerHTML = '<p class="ddi-summary-muted">No detailed mechanism summary available for this pair.</p>';
    }
}

function updateUI(data) {
    // 1. Update 2D SVG Molecule Graphic
    const svgContainer = document.getElementById('svg-container');
    if (data.svg) {
        svgContainer.innerHTML = data.svg;
    }
    
    document.getElementById('molecule-meta').textContent = `${data.num_atoms} Atoms | Model: ${data.arch}`;

    // 2. Update Endpoints Grid
    const grid = document.getElementById('endpoints-grid');
    grid.innerHTML = '';

    let safeCount = 0;
    let toxicCount = 0;

    data.predictions.forEach(p => {
        const isToxic = p.probability >= 0.5;
        if (isToxic) toxicCount++; else safeCount++;

        const card = document.createElement('div');
        card.className = 'endpoint-card';

        const percent = (p.probability * 100).toFixed(1);
        const statusClass = isToxic ? 'status-toxic' : 'status-safe';
        const fillClass = isToxic ? 'fill-toxic' : 'fill-safe';

        card.innerHTML = `
            <div class="endpoint-top">
                <span class="endpoint-title">${p.task}</span>
                <span class="status-badge ${statusClass}">${p.status}</span>
            </div>
            <div class="prob-meter">
                <div class="prob-fill ${fillClass}" style="width: ${percent}%;"></div>
            </div>
            <div class="endpoint-footer">
                <span>Probability: <strong>${percent}%</strong></span>
                <span>Risk: ${p.level}</span>
            </div>
        `;

        grid.appendChild(card);
    });

    // 3. Update Summary Stat Counters
    document.getElementById('stat-safe-count').innerHTML = `<i class="fa-solid fa-check"></i> ${safeCount} Safe`;
    document.getElementById('stat-toxic-count').innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${toxicCount} Toxic`;
}
