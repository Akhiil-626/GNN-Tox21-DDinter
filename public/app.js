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
    document.getElementById('btn-check-interaction').addEventListener('click', runInteractionCheck);
    document.getElementById('btn-resolve-name').addEventListener('click', resolveCompoundName);
    document.getElementById('task-select').addEventListener('change', runPrediction);
    document.getElementById('smiles-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runPrediction();
    });

    // Run initial prediction for default Aspirin molecule
    runPrediction();

    // Initialize Prescription Checker
    initPrescriptionChecker();
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

async function runInteractionCheck() {
    const recordRow = document.getElementById('ddi-record');
    if (recordRow) {
        recordRow.hidden = true;
    }

    const nameA = document.getElementById('ddi-name-a').value.trim();
    const nameB = document.getElementById('ddi-name-b').value.trim();
    const arch = document.getElementById('ddi-arch-select').value;
    const btn = document.getElementById('btn-check-interaction');
    const status = document.getElementById('ddi-status');
    const result = document.getElementById('ddi-result');
    const severityRow = result.querySelector('.severity-row');

    result.hidden = true;
    if (severityRow) {
        severityRow.innerHTML = '';
    }

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

        renderSeverity(data);
        renderDecisionNote(data.decision);
        renderRiskPanel(data.risk_overlap);
        renderRecord(data.ddinter_record);
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

const runInteractionPrediction = runInteractionCheck;

function renderSeverity(data) {
    const severityRow = document.querySelector('#ddi-result .severity-row');
    if (!severityRow) return;

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

    severityRow.innerHTML = `
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
}

// ---- Order-independent model: abstain note + "Why is this pair risky?" panel -------------------
// Everything below is built with textContent (never innerHTML) because drug names and
// assay labels are inserted into the page.

function renderDecisionNote(decision) {
    const row = document.querySelector('#ddi-result .severity-row');
    if (!row) return;
    const old = document.getElementById('ddi-decision');
    if (old) old.remove();
    if (!decision) return;   // original model in use: no calibrated abstain information

    const box = document.createElement('div');
    box.id = 'ddi-decision';
    box.className = 'ddi-decision ' + (decision.answered ? 'confident' : 'uncertain');
    const title = document.createElement('strong');
    const sub = document.createElement('span');
    const pct = Math.round((decision.coverage_target || 0.9) * 100);
    if (decision.answered) {
        title.textContent = 'Confident answer';
        sub.textContent = `Only one severity stays plausible at the ${pct}% confidence level.`;
    } else {
        title.textContent = 'Uncertain - treat the label above with caution';
        const set = (decision.prediction_set || []).join(' or ');
        sub.textContent = set
            ? `At the ${pct}% confidence level the severity could be: ${set}.`
            : `No single severity can be recommended at the ${pct}% confidence level.`;
    }
    box.appendChild(title);
    box.appendChild(sub);
    row.insertBefore(box, row.firstChild);
}

function buildRiskNode(risk, compact) {
    const wrap = document.createElement('div');
    wrap.className = 'risk-overlap' + (compact ? ' compact' : '');

    const head = document.createElement('div');
    head.className = 'risk-head';
    const title = document.createElement('strong');
    title.textContent = 'Shared predicted lab-assay risk (experimental)';
    const badge = document.createElement('span');
    badge.className = 'risk-badge risk-' + risk.level;
    const labels = { none: 'No shared risk signal', low: 'Low overlap', elevated: 'Elevated overlap', high: 'High overlap' };
    badge.textContent = labels[risk.level] || risk.level;
    head.appendChild(title);
    head.appendChild(badge);
    wrap.appendChild(head);

    const summary = document.createElement('p');
    summary.className = 'risk-summary';
    summary.textContent = `Expected shared risk: ${risk.expected_shared.toFixed(2)} of 12 lab-assay endpoints; `
        + `${risk.shared_flagged} flagged for both drugs.`;
    wrap.appendChild(summary);

    if (risk.shared && risk.shared.length) {
        const list = document.createElement('ul');
        list.className = 'risk-list';
        risk.shared.forEach(item => {
            const li = document.createElement('li');
            const name = document.createElement('span');
            name.className = 'risk-name';
            name.textContent = item.label;
            const detail = document.createElement('span');
            detail.className = 'risk-detail';
            detail.textContent = `${item.task}: ${(item.prob_a * 100).toFixed(0)}% and ${(item.prob_b * 100).toFixed(0)}%`;
            li.appendChild(name);
            li.appendChild(detail);
            list.appendChild(li);
        });
        wrap.appendChild(list);
    } else {
        const none = document.createElement('p');
        none.className = 'risk-none';
        none.textContent = 'Neither drug shares a strongly predicted lab-assay risk with the other.';
        wrap.appendChild(none);
    }

    if (!compact) {
        const cav = document.createElement('p');
        cav.className = 'risk-caveat';
        cav.textContent = risk.caveat;
        wrap.appendChild(cav);
    }
    return wrap;
}

function renderRiskPanel(risk) {
    const panel = document.getElementById('ddi-risk');
    if (!panel) return;
    panel.replaceChildren();
    if (!risk) {
        panel.hidden = true;
        return;
    }
    panel.appendChild(buildRiskNode(risk, false));
    panel.hidden = false;
}

function renderRecord(record) {
    const row = document.getElementById('ddi-record');
    if (!row) return;

    if (!record || !record.status || record.status === 'unavailable') {
        row.hidden = true;
        return;
    }

    const badge = document.getElementById('ddi-record-badge');
    const textEl = document.getElementById('ddi-record-text');
    const noteEl = document.getElementById('ddi-record-note');

    // Remove any previously appended attribution element
    const oldAttr = row.querySelector('.record-attribution');
    if (oldAttr) {
        oldAttr.remove();
    }

    if (record.status === 'match') {
        if (badge) {
            badge.hidden = false;
            badge.textContent = (record.all_levels || []).join(' / ');
            const sevClass = record.level ? `sev-${record.level.toLowerCase()}` : '';
            badge.className = `severity-badge small ${sevClass}`.trim();
        }
        if (textEl) {
            let msg = record.agrees_with_prediction
                ? "Matches the model's prediction."
                : "Differs from the model's prediction.";
            if (record.all_levels && record.all_levels.length > 1) {
                msg += " DDInter lists more than one rating for this pair.";
            }
            textEl.textContent = msg;
        }
        if (noteEl) {
            noteEl.hidden = false;
            noteEl.textContent = "This pair may have been part of the model's training data, so agreement is not a measure of accuracy.";
        }
    } else if (record.status === 'unknown_severity') {
        if (badge) {
            badge.hidden = true;
            badge.textContent = '';
        }
        if (textEl) {
            textEl.textContent = "DDInter lists this pair but gives no severity rating.";
        }
        if (noteEl) {
            noteEl.hidden = true;
            noteEl.textContent = '';
        }
    } else if (record.status === 'not_recorded') {
        if (badge) {
            badge.hidden = true;
            badge.textContent = '';
        }
        if (textEl) {
            textEl.textContent = "This pair is not in DDInter. That means undocumented, not confirmed safe.";
        }
        if (noteEl) {
            noteEl.hidden = true;
            noteEl.textContent = '';
        }
    } else {
        row.hidden = true;
        return;
    }

    // Append attribution built with DOM methods
    const attr = document.createElement('p');
    attr.className = 'record-attribution field-note';
    attr.appendChild(document.createTextNode('Source: '));
    const link = document.createElement('a');
    link.href = 'https://ddinter.scbdd.com';
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'DDInter';
    attr.appendChild(link);
    attr.appendChild(document.createTextNode(', CC BY-NC-SA 4.0'));
    row.appendChild(attr);

    row.hidden = false;
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

/* ==========================================================================
   Prescription Checker (rx-*)
   ========================================================================== */

let rxDrugs = [];
let selectedRxArch = 'gcn';
let rxDebounceTimer = null;
let rxActiveSuggestionIndex = -1;
let rxCurrentSuggestions = [];

function initPrescriptionChecker() {
    const rxInput = document.getElementById('rx-input');
    const btnCheck = document.getElementById('rx-btn-check');
    const btnClear = document.getElementById('rx-btn-clear');
    const example1 = document.getElementById('rx-example-1');
    const example2 = document.getElementById('rx-example-2');
    const btnDownload = document.getElementById('rx-btn-download-chart');

    if (!rxInput) return;

    rxInput.addEventListener('input', handleRxInput);
    rxInput.addEventListener('keydown', handleRxKeydown);
    document.addEventListener('click', handleRxOutsideClick);

    if (btnCheck) btnCheck.addEventListener('click', runPrescriptionCheck);
    if (btnClear) btnClear.addEventListener('click', clearPrescriptionChecker);
    if (btnDownload) btnDownload.addEventListener('click', downloadRelationChart);

    if (example1) {
        example1.addEventListener('click', () => {
            loadRxExample(['Abacavir', 'Ethanol', 'Cobicistat', 'Lamivudine']);
        });
    }
    if (example2) {
        example2.addEventListener('click', () => {
            loadRxExample(['Dolutegravir', 'Magnesium carbonate', 'Calcium acetate']);
        });
    }

    const archButtons = document.querySelectorAll('.rx-arch-btn');
    archButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            archButtons.forEach(b => b.classList.remove('rx-arch-active'));
            btn.classList.add('rx-arch-active');
            selectedRxArch = btn.dataset.arch || 'gcn';
        });
    });

    // Verify DDInter dataset availability; hide the panel if local data files are missing
    fetch('/api/ddinter/suggest?q=eth')
        .then(res => res.json())
        .then(data => {
            const rxPanel = document.getElementById('rx-panel');
            if (rxPanel && (!data.suggestions || data.suggestions.length === 0)) {
                rxPanel.hidden = true;
            }
        })
        .catch(() => {
            const rxPanel = document.getElementById('rx-panel');
            if (rxPanel) rxPanel.hidden = true;
        });
}

function handleRxInput(e) {
    clearTimeout(rxDebounceTimer);
    const query = e.target.value.trim();
    if (query.length < 3) {
        hideRxSuggestions();
        return;
    }
    rxDebounceTimer = setTimeout(async () => {
        await fetchRxSuggestions(query);
    }, 250);
}

async function fetchRxSuggestions(query) {
    const suggestionsUl = document.getElementById('rx-suggestions');
    if (!suggestionsUl) return;

    try {
        const res = await fetch(`/api/ddinter/suggest?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        renderRxSuggestions(data.suggestions || []);
    } catch (err) {
        console.error('Failed to fetch autocomplete suggestions:', err);
        hideRxSuggestions();
    }
}

function renderRxSuggestions(suggestions) {
    const suggestionsUl = document.getElementById('rx-suggestions');
    if (!suggestionsUl) return;

    while (suggestionsUl.firstChild) {
        suggestionsUl.removeChild(suggestionsUl.firstChild);
    }

    rxCurrentSuggestions = suggestions;
    rxActiveSuggestionIndex = -1;

    if (!suggestions || suggestions.length === 0) {
        suggestionsUl.hidden = true;
        return;
    }

    suggestions.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = 'rx-suggestion-item';
        li.setAttribute('role', 'option');

        const nameSpan = document.createElement('span');
        nameSpan.textContent = item.name;

        const idSpan = document.createElement('span');
        idSpan.className = 'rx-suggestion-id';
        idSpan.textContent = item.id;

        li.appendChild(nameSpan);
        li.appendChild(idSpan);

        li.addEventListener('click', () => {
            addRxDrug(item.name);
        });

        suggestionsUl.appendChild(li);
    });

    suggestionsUl.hidden = false;
}

function hideRxSuggestions() {
    const suggestionsUl = document.getElementById('rx-suggestions');
    if (suggestionsUl) {
        suggestionsUl.hidden = true;
        while (suggestionsUl.firstChild) {
            suggestionsUl.removeChild(suggestionsUl.firstChild);
        }
    }
    rxCurrentSuggestions = [];
    rxActiveSuggestionIndex = -1;
}

function handleRxKeydown(e) {
    const suggestionsUl = document.getElementById('rx-suggestions');
    const items = suggestionsUl ? suggestionsUl.querySelectorAll('.rx-suggestion-item') : [];

    if (e.key === 'ArrowDown') {
        if (!suggestionsUl || suggestionsUl.hidden || items.length === 0) return;
        e.preventDefault();
        rxActiveSuggestionIndex = (rxActiveSuggestionIndex + 1) % items.length;
        updateRxActiveSuggestion(items);
    } else if (e.key === 'ArrowUp') {
        if (!suggestionsUl || suggestionsUl.hidden || items.length === 0) return;
        e.preventDefault();
        rxActiveSuggestionIndex = (rxActiveSuggestionIndex - 1 + items.length) % items.length;
        updateRxActiveSuggestion(items);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (rxActiveSuggestionIndex >= 0 && rxActiveSuggestionIndex < rxCurrentSuggestions.length) {
            addRxDrug(rxCurrentSuggestions[rxActiveSuggestionIndex].name);
        } else {
            const raw = e.target.value.trim();
            if (raw) {
                addRxDrug(raw);
            }
        }
    } else if (e.key === 'Escape') {
        hideRxSuggestions();
    }
}

function updateRxActiveSuggestion(items) {
    items.forEach((item, idx) => {
        if (idx === rxActiveSuggestionIndex) {
            item.classList.add('rx-suggestion-active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('rx-suggestion-active');
        }
    });
}

function handleRxOutsideClick(e) {
    const wrapper = document.querySelector('.rx-autocomplete-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
        hideRxSuggestions();
    }
}

function addRxDrug(name) {
    const status = document.getElementById('rx-status');
    const rxInput = document.getElementById('rx-input');
    const clean = name.trim();

    if (!clean) return;

    if (rxDrugs.length >= 5) {
        if (status) {
            status.textContent = 'Maximum 5 drugs allowed for prescription screening.';
            status.className = 'rx-status error';
        }
        return;
    }

    if (rxDrugs.some(d => d.toLowerCase() === clean.toLowerCase())) {
        if (status) {
            status.textContent = `Drug "${clean}" is already added.`;
            status.className = 'rx-status error';
        }
        return;
    }

    rxDrugs.push(clean);
    if (status) {
        status.textContent = '';
        status.className = 'rx-status';
    }
    if (rxInput) {
        rxInput.value = '';
    }
    hideRxSuggestions();
    renderRxChips();
}

function removeRxDrug(index) {
    rxDrugs.splice(index, 1);
    renderRxChips();
}

function renderRxChips() {
    const container = document.getElementById('rx-chips-container');
    if (!container) return;

    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }

    rxDrugs.forEach((drugName, idx) => {
        const chip = document.createElement('span');
        chip.className = 'rx-chip';

        const nameSpan = document.createElement('span');
        nameSpan.textContent = drugName;
        chip.appendChild(nameSpan);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'rx-chip-remove';
        removeBtn.setAttribute('aria-label', `Remove ${drugName}`);
        removeBtn.textContent = '×';
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeRxDrug(idx);
        });
        chip.appendChild(removeBtn);

        container.appendChild(chip);
    });
}

function loadRxExample(drugs) {
    rxDrugs = [...drugs];
    renderRxChips();
    const status = document.getElementById('rx-status');
    if (status) {
        status.textContent = '';
        status.className = 'rx-status';
    }
    runPrescriptionCheck();
}

function clearPrescriptionChecker() {
    rxDrugs = [];
    renderRxChips();
    const rxInput = document.getElementById('rx-input');
    if (rxInput) rxInput.value = '';
    hideRxSuggestions();

    const status = document.getElementById('rx-status');
    if (status) {
        status.textContent = '';
        status.className = 'rx-status';
    }

    const results = document.getElementById('rx-results');
    if (results) results.hidden = true;
}

async function runPrescriptionCheck() {
    const status = document.getElementById('rx-status');
    const results = document.getElementById('rx-results');
    const btnCheck = document.getElementById('rx-btn-check');

    if (results) results.hidden = true;

    if (rxDrugs.length < 2) {
        if (status) {
            status.textContent = 'Add between 2 and 5 drugs to check prescription interactions.';
            status.className = 'rx-status error';
        }
        return;
    }

    if (btnCheck) {
        btnCheck.disabled = true;
        btnCheck.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking interactions...';
    }
    if (status) {
        status.textContent = 'Resolving chemical structures and querying DDInter...';
        status.className = 'rx-status';
    }

    try {
        const res = await fetch('/api/check-prescription', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ names: rxDrugs, arch: selectedRxArch })
        });
        const data = await res.json();

        if (!res.ok) {
            if (status) {
                status.textContent = data.error || 'Failed to check prescription interactions.';
                status.className = 'rx-status error';
            }
            return;
        }

        if (status) {
            status.textContent = '';
            status.className = 'rx-status';
        }
        renderPrescriptionResults(data);
    } catch (err) {
        console.error('Prescription checker error:', err);
        if (status) {
            status.textContent = 'Failed to connect to backend server.';
            status.className = 'rx-status error';
        }
    } finally {
        if (btnCheck) {
            btnCheck.disabled = false;
            btnCheck.innerHTML = '<i class="fa-solid fa-stethoscope"></i> Get interactions';
        }
    }
}

function renderPrescriptionResults(data) {
    const results = document.getElementById('rx-results');
    if (!results) return;

    // 1. Warnings
    const warningsEl = document.getElementById('rx-warnings');
    if (warningsEl) {
        while (warningsEl.firstChild) warningsEl.removeChild(warningsEl.firstChild);
        if (data.warnings && data.warnings.length > 0) {
            data.warnings.forEach(w => {
                const p = document.createElement('p');
                p.textContent = w;
                warningsEl.appendChild(p);
            });
            warningsEl.hidden = false;
        } else {
            warningsEl.hidden = true;
        }
    }

    // 2. Relation Chart
    renderRelationChart(data.drugs || [], data.pairs || []);

    // 3. Per-drug Distribution Bars
    renderDistributions(data.drugs || []);

    // 4. Pairwise Cards
    renderPairCards(data.drugs || [], data.pairs || []);

    results.hidden = false;
}

function renderRelationChart(drugs, pairs) {
    const container = document.getElementById('rx-relation-container');
    if (!container) return;

    while (container.firstChild) container.removeChild(container.firstChild);

    const n = drugs.length;
    if (n < 2) return;

    const width = 460;
    const height = 310;
    const svgNS = 'http://www.w3.org/2000/svg';

    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '310');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `Interaction network diagram for ${drugs.map(d => d.name).join(', ')}`);

    // Calculate node coordinates
    const nodes = [];
    if (n === 2) {
        nodes.push({ x: 130, y: 135 });
        nodes.push({ x: 330, y: 135 });
    } else {
        const cx = 230;
        const cy = 130;
        const radius = 80;
        for (let i = 0; i < n; i++) {
            const angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
            nodes.push({
                x: cx + radius * Math.cos(angle),
                y: cy + radius * Math.sin(angle)
            });
        }
    }

    // Draw Edges
    pairs.forEach(pair => {
        const p1 = nodes[pair.a];
        const p2 = nodes[pair.b];
        if (!p1 || !p2) return;

        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', p1.x);
        line.setAttribute('y1', p1.y);
        line.setAttribute('x2', p2.x);
        line.setAttribute('y2', p2.y);

        const status = pair.record ? pair.record.status : 'not_recorded';
        const level = pair.record ? pair.record.level : null;

        if (status === 'match') {
            if (level === 'Major') {
                line.setAttribute('stroke', '#A23327');
                line.setAttribute('stroke-width', '6.5');
            } else if (level === 'Moderate') {
                line.setAttribute('stroke', '#A16A17');
                line.setAttribute('stroke-width', '4.5');
            } else {
                line.setAttribute('stroke', '#2F7D5C');
                line.setAttribute('stroke-width', '3');
            }
        } else if (status === 'unknown_severity') {
            line.setAttribute('stroke', '#888888');
            line.setAttribute('stroke-width', '2.5');
            line.setAttribute('stroke-dasharray', '6,4');
        } else {
            // not_recorded or not_in_ddinter
            line.setAttribute('stroke', '#475569');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('stroke-dasharray', '4,4');
        }

        svg.appendChild(line);
    });

    // Draw Nodes
    drugs.forEach((drug, idx) => {
        const pt = nodes[idx];
        if (!pt) return;

        const g = document.createElementNS(svgNS, 'g');

        const circle = document.createElementNS(svgNS, 'circle');
        circle.setAttribute('cx', pt.x);
        circle.setAttribute('cy', pt.y);
        circle.setAttribute('r', '22');
        circle.setAttribute('fill', '#1e293b');
        circle.setAttribute('stroke', '#06b6d4');
        circle.setAttribute('stroke-width', '2');

        const text = document.createElementNS(svgNS, 'text');
        text.setAttribute('x', pt.x);
        text.setAttribute('y', pt.y + 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#f8fafc');
        text.setAttribute('font-size', '10');
        text.setAttribute('font-weight', '600');
        text.setAttribute('font-family', 'sans-serif');

        const displayName = drug.name || drug.input;
        text.textContent = displayName.length > 9 ? displayName.slice(0, 8) + '…' : displayName;

        const title = document.createElementNS(svgNS, 'title');
        title.textContent = displayName;
        g.appendChild(title);

        g.appendChild(circle);
        g.appendChild(text);
        svg.appendChild(g);
    });

    // Draw Legend at bottom
    const legendG = document.createElementNS(svgNS, 'g');
    legendG.setAttribute('transform', 'translate(10, 268)');

    const legendItems = [
        { label: 'Major', color: '#A23327', width: '5', dash: '' },
        { label: 'Moderate', color: '#A16A17', width: '4', dash: '' },
        { label: 'Minor', color: '#2F7D5C', width: '3', dash: '' },
        { label: 'Unrated', color: '#888888', width: '2', dash: '4,3' },
        { label: 'Not in DDInter', color: '#475569', width: '2', dash: '3,3' }
    ];

    let legX = 15;
    legendItems.forEach(item => {
        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', legX);
        line.setAttribute('y1', 10);
        line.setAttribute('x2', legX + 20);
        line.setAttribute('y2', 10);
        line.setAttribute('stroke', item.color);
        line.setAttribute('stroke-width', item.width);
        if (item.dash) line.setAttribute('stroke-dasharray', item.dash);

        const txt = document.createElementNS(svgNS, 'text');
        txt.setAttribute('x', legX + 26);
        txt.setAttribute('y', 14);
        txt.setAttribute('fill', '#94a3b8');
        txt.setAttribute('font-size', '10');
        txt.setAttribute('font-family', 'sans-serif');
        txt.textContent = item.label;

        legendG.appendChild(line);
        legendG.appendChild(txt);
        legX += item.label.length * 6 + 46;
    });

    svg.appendChild(legendG);
    container.appendChild(svg);
}

function downloadRelationChart() {
    const container = document.getElementById('rx-relation-container');
    const svg = container ? container.querySelector('svg') : null;
    if (!svg) return;

    const clone = svg.cloneNode(true);
    const svgNS = 'http://www.w3.org/2000/svg';
    const bgRect = document.createElementNS(svgNS, 'rect');
    bgRect.setAttribute('width', '100%');
    bgRect.setAttribute('height', '100%');
    bgRect.setAttribute('fill', '#131f3e');
    clone.insertBefore(bgRect, clone.firstChild);

    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clone);
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const URLObj = window.URL || window.webkitURL || window;
    const blobURL = URLObj.createObjectURL(svgBlob);

    const img = new Image();
    img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = 920;
        canvas.height = 620;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, 920, 620);
        URLObj.revokeObjectURL(blobURL);

        const pngURL = canvas.toDataURL('image/png');
        const dlLink = document.createElement('a');
        dlLink.download = 'prescription_relation_chart.png';
        dlLink.href = pngURL;
        document.body.appendChild(dlLink);
        dlLink.click();
        document.body.removeChild(dlLink);
    };
    img.src = blobURL;
}

function renderDistributions(drugs) {
    const container = document.getElementById('rx-dist-container');
    if (!container) return;

    while (container.firstChild) container.removeChild(container.firstChild);

    drugs.forEach(drug => {
        const row = document.createElement('div');
        row.className = 'rx-dist-row';

        const meta = document.createElement('div');
        meta.className = 'rx-dist-meta';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'rx-dist-drug-name';
        nameSpan.textContent = drug.name || drug.input;
        meta.appendChild(nameSpan);

        const countSpan = document.createElement('span');
        countSpan.className = 'rx-dist-counts';

        const dist = drug.distribution;
        if (dist && dist.total > 0) {
            countSpan.textContent = `Major: ${dist.Major} | Mod: ${dist.Moderate} | Min: ${dist.Minor} | Unrated: ${dist.Unrated} (Total: ${dist.total})`;
            meta.appendChild(countSpan);
            row.appendChild(meta);

            const bar = document.createElement('div');
            bar.className = 'rx-dist-bar';
            bar.setAttribute('role', 'progressbar');
            bar.setAttribute('aria-label', `Interaction severity breakdown for ${drug.name}`);

            const total = dist.total;
            const segs = [
                { cls: 'rx-dist-seg-major', val: dist.Major, title: `Major: ${dist.Major}` },
                { cls: 'rx-dist-seg-moderate', val: dist.Moderate, title: `Moderate: ${dist.Moderate}` },
                { cls: 'rx-dist-seg-minor', val: dist.Minor, title: `Minor: ${dist.Minor}` },
                { cls: 'rx-dist-seg-unrated', val: dist.Unrated, title: `Unrated: ${dist.Unrated}` }
            ];

            segs.forEach(seg => {
                if (seg.val > 0) {
                    const div = document.createElement('div');
                    div.className = seg.cls;
                    div.style.width = `${(seg.val / total) * 100}%`;
                    div.title = seg.title;
                    bar.appendChild(div);
                }
            });
            row.appendChild(bar);
        } else if (drug.ddinter_id) {
            countSpan.textContent = '0 recorded interactions in DDInter';
            meta.appendChild(countSpan);
            row.appendChild(meta);
        } else {
            countSpan.textContent = 'Not in DDInter database';
            meta.appendChild(countSpan);
            row.appendChild(meta);
        }

        container.appendChild(row);
    });
}

function renderPairCards(drugs, pairs) {
    const container = document.getElementById('rx-pairs-grid');
    if (!container) return;

    while (container.firstChild) container.removeChild(container.firstChild);

    pairs.forEach(pair => {
        const drugA = drugs[pair.a];
        const drugB = drugs[pair.b];
        if (!drugA || !drugB) return;

        const card = document.createElement('div');
        card.className = 'rx-pair-card';

        // Pair Top: Names + Severity Badge
        const top = document.createElement('div');
        top.className = 'rx-pair-top';

        const names = document.createElement('div');
        names.className = 'rx-pair-names';
        names.textContent = `${drugA.name || drugA.input} + ${drugB.name || drugB.input}`;
        top.appendChild(names);

        const badge = document.createElement('span');
        badge.className = 'severity-badge small';
        const rec = pair.record || {};

        if (rec.status === 'match') {
            badge.textContent = (rec.all_levels || []).join(' / ');
            const lvlClass = rec.level ? `sev-${rec.level.toLowerCase()}` : '';
            badge.className = `severity-badge small ${lvlClass}`.trim();
        } else if (rec.status === 'unknown_severity') {
            badge.textContent = 'Unrated';
            badge.className = 'severity-badge small sev-moderate';
        } else if (rec.status === 'not_recorded') {
            badge.textContent = 'Not recorded';
            badge.className = 'severity-badge small';
            badge.style.background = 'rgba(255,255,255,0.06)';
            badge.style.color = 'var(--text-muted)';
        } else {
            badge.textContent = 'Not in DDInter';
            badge.className = 'severity-badge small';
            badge.style.background = 'rgba(255,255,255,0.06)';
            badge.style.color = 'var(--text-muted)';
        }
        top.appendChild(badge);
        card.appendChild(top);

        // Record description text
        const desc = document.createElement('p');
        desc.className = 'rx-record-desc';
        if (rec.status === 'match') {
            desc.textContent = `DDInter records this combination as ${rec.all_levels.join(' / ')} severity.`;
        } else if (rec.status === 'unknown_severity') {
            desc.textContent = 'DDInter lists this pair in literature but provides no confirmed severity rating.';
        } else if (rec.status === 'not_recorded') {
            desc.textContent = 'This specific pair is not recorded in the DDInter interaction dataset.';
        } else {
            desc.textContent = 'At least one of these compounds is not documented in the DDInter repository.';
        }
        card.appendChild(desc);

        // Model Estimate Block
        const modelBlock = document.createElement('div');
        modelBlock.className = 'rx-model-estimate';

        if (pair.model) {
            const strong = document.createElement('strong');
            const dec = pair.model.decision;
            if (dec && !dec.answered) {
                const set = (dec.prediction_set || []).join(' or ');
                strong.textContent = set ? `Model: uncertain - could be ${set}` : 'Model: uncertain';
            } else {
                strong.textContent = `Model: ${pair.model.label} Severity`;
            }
            modelBlock.appendChild(strong);

            const probs = pair.model.probabilities || {};
            const probStr = Object.entries(probs)
                .map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`)
                .join(' | ');
            const probP = document.createElement('span');
            probP.textContent = probStr;
            modelBlock.appendChild(probP);

            const note = document.createElement('span');
            note.style.fontSize = '11px';
            note.style.fontStyle = 'italic';
            note.textContent = 'assumes an interaction exists; the model was trained only on interacting pairs';
            modelBlock.appendChild(note);

            if (pair.model.risk_overlap) {
                modelBlock.appendChild(buildRiskNode(pair.model.risk_overlap, true));
            }
        } else {
            const noModel = document.createElement('span');
            noModel.textContent = 'Model estimate unavailable (requires valid SMILES chemical structure for both compounds).';
            modelBlock.appendChild(noModel);
        }
        card.appendChild(modelBlock);

        // Details URL
        if (pair.details_url) {
            const link = document.createElement('a');
            link.className = 'rx-details-link';
            link.href = pair.details_url;
            link.target = '_blank';
            link.rel = 'noopener';

            const linkIcon = document.createElement('i');
            linkIcon.className = 'fa-solid fa-arrow-up-right-from-square';
            link.appendChild(linkIcon);

            const linkText = document.createTextNode(' See mechanism and management on DDInter');
            link.appendChild(linkText);
            card.appendChild(link);
        }

        // Analogue Block for not_recorded pairs
        if (pair.analogues) {
            const analogueBlock = document.createElement('div');
            analogueBlock.className = 'rx-analogue-block';

            const summaryP = document.createElement('p');
            summaryP.className = 'rx-analogue-summary';
            summaryP.textContent = pair.analogues.summary || '';
            analogueBlock.appendChild(summaryP);

            const graphDiv = document.createElement('div');
            graphDiv.className = 'rx-analogue-graph';
            renderAnalogueGraph(graphDiv, drugA.name || drugA.input, drugB.name || drugB.input, pair.analogues);
            analogueBlock.appendChild(graphDiv);

            card.appendChild(analogueBlock);
        }

        container.appendChild(card);
    });
}

function renderAnalogueGraph(container, nameA, nameB, analogues) {
    const simA = analogues.similar_to_a || [];
    const simB = analogues.similar_to_b || [];
    if (simA.length === 0 && simB.length === 0) return;

    const count = Math.max(simA.length, simB.length);
    const height = Math.max(110, count * 36 + 20);
    const width = 380;
    const svgNS = 'http://www.w3.org/2000/svg';

    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', height.toString());
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `Structural analogue graph connecting ${nameA} and ${nameB} via related compounds`);

    const yA = height / 2;
    const yB = height / 2;
    const ptA = { x: 50, y: yA };
    const ptB = { x: 330, y: yB };

    // Draw analogues similar to A
    simA.forEach((item, idx) => {
        const y = (height / (simA.length + 1)) * (idx + 1);
        const x = 145;

        // Dotted line from A to similar drug
        const lineSim = document.createElementNS(svgNS, 'line');
        lineSim.setAttribute('x1', ptA.x);
        lineSim.setAttribute('y1', ptA.y);
        lineSim.setAttribute('x2', x);
        lineSim.setAttribute('y2', y);
        lineSim.setAttribute('stroke', '#64748b');
        lineSim.setAttribute('stroke-width', '1.5');
        lineSim.setAttribute('stroke-dasharray', '3,3');
        svg.appendChild(lineSim);

        const txtSim = document.createElementNS(svgNS, 'text');
        txtSim.setAttribute('x', (ptA.x + x) / 2);
        txtSim.setAttribute('y', (ptA.y + y) / 2 - 4);
        txtSim.setAttribute('fill', '#94a3b8');
        txtSim.setAttribute('font-size', '9');
        txtSim.setAttribute('text-anchor', 'middle');
        txtSim.textContent = `${(item.similarity * 100).toFixed(0)}%`;
        svg.appendChild(txtSim);

        // Line from similar drug to B
        const linePartner = document.createElementNS(svgNS, 'line');
        linePartner.setAttribute('x1', x);
        linePartner.setAttribute('y1', y);
        linePartner.setAttribute('x2', ptB.x);
        linePartner.setAttribute('y2', ptB.y);

        if (item.level_with_b === 'Major') {
            linePartner.setAttribute('stroke', '#A23327');
            linePartner.setAttribute('stroke-width', '3');
        } else if (item.level_with_b === 'Moderate') {
            linePartner.setAttribute('stroke', '#A16A17');
            linePartner.setAttribute('stroke-width', '2.5');
        } else if (item.level_with_b === 'Minor') {
            linePartner.setAttribute('stroke', '#2F7D5C');
            linePartner.setAttribute('stroke-width', '2');
        } else if (item.level_with_b === 'Unrated') {
            linePartner.setAttribute('stroke', '#888888');
            linePartner.setAttribute('stroke-width', '1.5');
            linePartner.setAttribute('stroke-dasharray', '4,3');
        } else {
            linePartner.setAttribute('stroke', '#334155');
            linePartner.setAttribute('stroke-width', '1');
            linePartner.setAttribute('stroke-dasharray', '3,3');
        }
        svg.appendChild(linePartner);

        // Similar drug node
        const c = document.createElementNS(svgNS, 'circle');
        c.setAttribute('cx', x);
        c.setAttribute('cy', y);
        c.setAttribute('r', '14');
        c.setAttribute('fill', '#0f172a');
        c.setAttribute('stroke', '#38bdf8');
        c.setAttribute('stroke-width', '1.5');

        const t = document.createElementNS(svgNS, 'text');
        t.setAttribute('x', x);
        t.setAttribute('y', y + 3);
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('fill', '#cbd5e1');
        t.setAttribute('font-size', '8');
        t.textContent = item.name.length > 7 ? item.name.slice(0, 6) + '…' : item.name;

        const title = document.createElementNS(svgNS, 'title');
        title.textContent = `${item.name} (${(item.similarity * 100).toFixed(1)}% similar to ${nameA})`;
        svg.appendChild(title);

        svg.appendChild(c);
        svg.appendChild(t);
    });

    // Draw analogues similar to B
    simB.forEach((item, idx) => {
        const y = (height / (simB.length + 1)) * (idx + 1);
        const x = 235;

        // Dotted line from B to similar drug
        const lineSim = document.createElementNS(svgNS, 'line');
        lineSim.setAttribute('x1', ptB.x);
        lineSim.setAttribute('y1', ptB.y);
        lineSim.setAttribute('x2', x);
        lineSim.setAttribute('y2', y);
        lineSim.setAttribute('stroke', '#64748b');
        lineSim.setAttribute('stroke-width', '1.5');
        lineSim.setAttribute('stroke-dasharray', '3,3');
        svg.appendChild(lineSim);

        const txtSim = document.createElementNS(svgNS, 'text');
        txtSim.setAttribute('x', (ptB.x + x) / 2);
        txtSim.setAttribute('y', (ptB.y + y) / 2 - 4);
        txtSim.setAttribute('fill', '#94a3b8');
        txtSim.setAttribute('font-size', '9');
        txtSim.setAttribute('text-anchor', 'middle');
        txtSim.textContent = `${(item.similarity * 100).toFixed(0)}%`;
        svg.appendChild(txtSim);

        // Line from similar drug to A
        const linePartner = document.createElementNS(svgNS, 'line');
        linePartner.setAttribute('x1', x);
        linePartner.setAttribute('y1', y);
        linePartner.setAttribute('x2', ptA.x);
        linePartner.setAttribute('y2', ptA.y);

        if (item.level_with_a === 'Major') {
            linePartner.setAttribute('stroke', '#A23327');
            linePartner.setAttribute('stroke-width', '3');
        } else if (item.level_with_a === 'Moderate') {
            linePartner.setAttribute('stroke', '#A16A17');
            linePartner.setAttribute('stroke-width', '2.5');
        } else if (item.level_with_a === 'Minor') {
            linePartner.setAttribute('stroke', '#2F7D5C');
            linePartner.setAttribute('stroke-width', '2');
        } else if (item.level_with_a === 'Unrated') {
            linePartner.setAttribute('stroke', '#888888');
            linePartner.setAttribute('stroke-width', '1.5');
            linePartner.setAttribute('stroke-dasharray', '4,3');
        } else {
            linePartner.setAttribute('stroke', '#334155');
            linePartner.setAttribute('stroke-width', '1');
            linePartner.setAttribute('stroke-dasharray', '3,3');
        }
        svg.appendChild(linePartner);

        // Similar drug node
        const c = document.createElementNS(svgNS, 'circle');
        c.setAttribute('cx', x);
        c.setAttribute('cy', y);
        c.setAttribute('r', '14');
        c.setAttribute('fill', '#0f172a');
        c.setAttribute('stroke', '#c084fc');
        c.setAttribute('stroke-width', '1.5');

        const t = document.createElementNS(svgNS, 'text');
        t.setAttribute('x', x);
        t.setAttribute('y', y + 3);
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('fill', '#cbd5e1');
        t.setAttribute('font-size', '8');
        t.textContent = item.name.length > 7 ? item.name.slice(0, 6) + '…' : item.name;

        const title = document.createElementNS(svgNS, 'title');
        title.textContent = `${item.name} (${(item.similarity * 100).toFixed(1)}% similar to ${nameB})`;
        svg.appendChild(title);

        svg.appendChild(c);
        svg.appendChild(t);
    });

    // Draw Main Nodes A and B
    [
        { pt: ptA, name: nameA, color: '#38bdf8' },
        { pt: ptB, name: nameB, color: '#c084fc' }
    ].forEach(node => {
        const c = document.createElementNS(svgNS, 'circle');
        c.setAttribute('cx', node.pt.x);
        c.setAttribute('cy', node.pt.y);
        c.setAttribute('r', '18');
        c.setAttribute('fill', '#1e293b');
        c.setAttribute('stroke', node.color);
        c.setAttribute('stroke-width', '2');

        const t = document.createElementNS(svgNS, 'text');
        t.setAttribute('x', node.pt.x);
        t.setAttribute('y', node.pt.y + 4);
        t.setAttribute('text-anchor', 'middle');
        t.setAttribute('fill', '#ffffff');
        t.setAttribute('font-size', '9');
        t.setAttribute('font-weight', '700');
        t.textContent = node.name.length > 8 ? node.name.slice(0, 7) + '…' : node.name;

        svg.appendChild(c);
        svg.appendChild(t);
    });

    container.appendChild(svg);
}
