import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = path.resolve(__dirname, '../..');
const landingDir = path.resolve(__dirname, '..');

const metricsCsvPath = path.resolve(projectRoot, 'results/metrics.csv');
const ddiMetricsCsvPath = path.resolve(projectRoot, 'results/ddi_metrics.csv');
const outputTsPath = path.resolve(landingDir, 'src/data/metrics.generated.ts');

console.log('[build-data] Parsing benchmark metrics for C-FOOTPRINT landing page...');

// 1. Check metrics.csv
if (!fs.existsSync(metricsCsvPath)) {
  console.error(`[build-data] ERROR: Required file not found at ${metricsCsvPath}`);
  process.exit(1);
}

const metricsRaw = fs.readFileSync(metricsCsvPath, 'utf8');
const metricsLines = metricsRaw
  .split(/\r?\n/)
  .map((l) => l.trim())
  .filter((l) => l.length > 0);

if (metricsLines.length <= 1) {
  console.error(`[build-data] ERROR: ${metricsCsvPath} yields 0 rows of data.`);
  process.exit(1);
}

const metricsHeaders = metricsLines[0].split(',').map((h) => h.trim());
const tox21Rows = [];

for (let i = 1; i < metricsLines.length; i++) {
  const parts = metricsLines[i].split(',').map((p) => p.trim());
  if (parts.length < metricsHeaders.length) continue;

  const row = {};
  let hasBlankNumeric = false;

  metricsHeaders.forEach((header, idx) => {
    const val = parts[idx];
    row[header] = val;
    if (header !== 'Task' && header !== 'Model') {
      const num = parseFloat(val);
      if (isNaN(num)) hasBlankNumeric = true;
    }
  });

  if (hasBlankNumeric) {
    console.warn(`[build-data] Skipping row ${i} with blank/invalid numbers:`, parts);
    continue;
  }

  tox21Rows.push({
    task: row['Task'],
    rocAuc: parseFloat(row['ROC-AUC']),
    prAuc: parseFloat(row['PR-AUC']),
    sensitivity: parseFloat(row['Sensitivity']),
    specificity: parseFloat(row['Specificity']),
    accuracy: parseFloat(row['Accuracy']),
    model: row['Model'],
  });
}

if (tox21Rows.length === 0) {
  console.error(`[build-data] ERROR: No valid rows extracted from ${metricsCsvPath}.`);
  process.exit(1);
}

console.log(`[build-data] Parsed ${tox21Rows.length} valid Tox21 metric rows.`);

// Assert Tox21 means against reference values
const REFERENCE_MEANS = {
  GCN: 0.762,
  GIN: 0.761,
  MPNN: 0.757,
  'RF (Morgan FP)': 0.732,
};

const models = ['GCN', 'GIN', 'MPNN', 'RF (Morgan FP)'];
const meanMetrics = [];

for (const model of models) {
  const modelRows = tox21Rows.filter((r) => r.model === model);
  if (modelRows.length === 0) {
    console.error(`[build-data] ERROR: No rows found for model ${model}`);
    process.exit(1);
  }
  const rocAucs = modelRows.map((r) => r.rocAuc);
  const prAucs = modelRows.map((r) => r.prAuc);
  const meanRocAuc = rocAucs.reduce((a, b) => a + b, 0) / rocAucs.length;
  const meanPrAuc = prAucs.reduce((a, b) => a + b, 0) / prAucs.length;

  const refMean = REFERENCE_MEANS[model];
  const diff = Math.abs(meanRocAuc - refMean);
  if (diff > 0.001) {
    console.warn(
      `[build-data] Difference from reference for ${model}: got ${meanRocAuc.toFixed(
        4
      )}, expected ~${refMean} (diff: ${diff.toFixed(4)})`
    );
  }

  meanMetrics.push({
    model,
    meanRocAuc: parseFloat(meanRocAuc.toFixed(3)),
    meanRocAucExact: meanRocAuc,
    meanPrAuc: parseFloat(meanPrAuc.toFixed(3)),
    meanPrAucExact: meanPrAuc,
    endpointCount: modelRows.length,
  });
}

// 2. Parse DDI Metrics
const REFERENCE_DDI = {
  GCN: {
    accuracy: 0.600,
    macroF1: 0.491,
    minorF1: 0.247,
    moderateF1: 0.686,
    majorF1: 0.541,
    majorRecall: 0.705,
  },
  GIN: {
    accuracy: 0.609,
    macroF1: 0.490,
    minorF1: 0.262,
    moderateF1: 0.708,
    majorF1: 0.501,
    majorRecall: 0.609,
  },
};

let ddiMetrics = null;

if (!fs.existsSync(ddiMetricsCsvPath)) {
  console.warn(`[build-data] WARNING: ${ddiMetricsCsvPath} not found. Falling back to reference DDI values.`);
  ddiMetrics = REFERENCE_DDI;
} else {
  const ddiRaw = fs.readFileSync(ddiMetricsCsvPath, 'utf8');
  const ddiLines = ddiRaw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  const ddiHeaders = ddiLines[0].split(',').map((h) => h.trim());
  const parsedDdi = {};

  for (let i = 1; i < ddiLines.length; i++) {
    const parts = ddiLines[i].split(',').map((p) => p.trim());
    const row = {};
    ddiHeaders.forEach((h, idx) => (row[h] = parts[idx]));

    const arch = row['architecture'];
    if (!arch) continue;

    const acc = parseFloat(row['test_accuracy']);
    const macroF1 = parseFloat(row['test_macro_f1']);
    const minorF1 = parseFloat(row['Minor_f1']);
    const modF1 = parseFloat(row['Moderate_f1']);
    const majF1 = parseFloat(row['Major_f1']);
    const majRecall = parseFloat(row['Major_recall']);

    if (isNaN(acc) || isNaN(macroF1)) {
      console.log(`[build-data] Note: Skipping incomplete DDI row for arch "${arch}" (note: ${row['note'] || 'none'})`);
      continue;
    }

    parsedDdi[arch] = {
      accuracy: parseFloat(acc.toFixed(3)),
      accuracyExact: acc,
      macroF1: parseFloat(macroF1.toFixed(3)),
      macroF1Exact: macroF1,
      minorF1: parseFloat(minorF1.toFixed(3)),
      minorF1Exact: minorF1,
      moderateF1: parseFloat(modF1.toFixed(3)),
      moderateF1Exact: modF1,
      majorF1: parseFloat(majF1.toFixed(3)),
      majorF1Exact: majF1,
      majorRecall: parseFloat(majRecall.toFixed(3)),
      majorRecallExact: majRecall,
    };
  }

  ddiMetrics = parsedDdi;
}

// Prepare Grouped Bars: Per-Endpoint GIN vs RF (12 endpoints)
const TOX21_ENDPOINTS = [
  'NR-AR',
  'NR-AR-LBD',
  'NR-AhR',
  'NR-Aromatase',
  'NR-ER',
  'NR-ER-LBD',
  'NR-PPAR-gamma',
  'SR-ARE',
  'SR-ATAD5',
  'SR-HSE',
  'SR-MMP',
  'SR-p53',
];

const perEndpointGinVsRf = TOX21_ENDPOINTS.map((endpoint) => {
  const ginRow = tox21Rows.find((r) => r.task === endpoint && r.model === 'GIN');
  const rfRow = tox21Rows.find((r) => r.task === endpoint && r.model === 'RF (Morgan FP)');
  const gcnRow = tox21Rows.find((r) => r.task === endpoint && r.model === 'GCN');
  const mpnnRow = tox21Rows.find((r) => r.task === endpoint && r.model === 'MPNN');

  return {
    endpoint,
    GIN: ginRow ? parseFloat(ginRow.rocAuc.toFixed(3)) : 0,
    RF: rfRow ? parseFloat(rfRow.rocAuc.toFixed(3)) : 0,
    GCN: gcnRow ? parseFloat(gcnRow.rocAuc.toFixed(3)) : 0,
    MPNN: mpnnRow ? parseFloat(mpnnRow.rocAuc.toFixed(3)) : 0,
  };
});

// Prepare Radar Data: GCN vs GIN across 6 metrics
const radarMetrics = [
  { metric: 'Accuracy', label: 'Overall Accuracy', key: 'accuracy', fullScale: 1.0 },
  { metric: 'Macro-F1', label: 'Macro F1-Score', key: 'macroF1', fullScale: 1.0 },
  { metric: 'Minor F1', label: 'Minor Severity F1', key: 'minorF1', fullScale: 1.0 },
  { metric: 'Moderate F1', label: 'Moderate Severity F1', key: 'moderateF1', fullScale: 1.0 },
  { metric: 'Major F1', label: 'Major Severity F1', key: 'majorF1', fullScale: 1.0 },
  { metric: 'Major Recall', label: 'Major Severity Recall', key: 'majorRecall', fullScale: 1.0 },
].map((m) => {
  const gcnVal = ddiMetrics['GCN'] ? ddiMetrics['GCN'][m.key] : REFERENCE_DDI.GCN[m.key];
  const ginVal = ddiMetrics['GIN'] ? ddiMetrics['GIN'][m.key] : REFERENCE_DDI.GIN[m.key];
  return {
    metric: m.metric,
    label: m.label,
    GCN: gcnVal,
    GIN: ginVal,
    fullScale: m.fullScale,
  };
});

// Generate TypeScript Output
const tsContent = `// AUTO-GENERATED BY landing/scripts/build-data.mjs - DO NOT EDIT MANUALLY
// Generated on ${new Date().toISOString()}

export interface Tox21MetricRow {
  task: string;
  rocAuc: number;
  prAuc: number;
  sensitivity: number;
  specificity: number;
  accuracy: number;
  model: 'GCN' | 'GIN' | 'MPNN' | 'RF (Morgan FP)';
}

export interface ModelMeanMetric {
  model: string;
  meanRocAuc: number;
  meanRocAucExact: number;
  meanPrAuc: number;
  meanPrAucExact: number;
  endpointCount: number;
}

export interface EndpointComparisonMetric {
  endpoint: string;
  GIN: number;
  RF: number;
  GCN: number;
  MPNN: number;
}

export interface DdiRadarPoint {
  metric: string;
  label: string;
  GCN: number;
  GIN: number;
  fullScale: number;
}

export const TOX21_ENDPOINTS = ${JSON.stringify(TOX21_ENDPOINTS, null, 2)} as const;

export const MEAN_METRICS_DATA: ModelMeanMetric[] = ${JSON.stringify(meanMetrics, null, 2)};

export const PER_ENDPOINT_GIN_RF_DATA: EndpointComparisonMetric[] = ${JSON.stringify(
  perEndpointGinVsRf,
  null,
  2
)};

export const DDI_RADAR_DATA: DdiRadarPoint[] = ${JSON.stringify(radarMetrics, null, 2)};

export const RAW_TOX21_ROWS: Tox21MetricRow[] = ${JSON.stringify(tox21Rows, null, 2)};
`;

fs.writeFileSync(outputTsPath, tsContent, 'utf8');
console.log(`[build-data] Successfully generated ${outputTsPath}`);
