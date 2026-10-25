// Typed build-time data extracted from results/metrics.csv and results/ddi_metrics.csv
// Follows strict fallback values specified in task requirements.

export interface ModelMeanMetric {
  model: string;
  name: string;
  meanRocAuc: number;
  meanPrAuc: number;
  description: string;
}

export interface EndpointMetric {
  endpoint: string;
  ginRocAuc: number;
  rfRocAuc: number;
  gcnRocAuc: number;
  mpnnRocAuc: number;
  fullTaskName: string;
}

export interface DdiRadarMetric {
  metric: string;
  label: string;
  gcn: number;
  gin: number;
  fullScale: number;
}

export const TOX21_ENDPOINTS = [
  "NR-AR",
  "NR-AR-LBD",
  "NR-AhR",
  "NR-Aromatase",
  "NR-ER",
  "NR-ER-LBD",
  "NR-PPAR-gamma",
  "SR-ARE",
  "SR-ATAD5",
  "SR-HSE",
  "SR-MMP",
  "SR-p53",
] as const;

export const MEAN_METRICS_DATA: ModelMeanMetric[] = [
  {
    model: "GCN",
    name: "Graph Convolutional Network",
    meanRocAuc: 0.762,
    meanPrAuc: 0.332,
    description: "Standard spatial message passing architecture",
  },
  {
    model: "GIN",
    name: "Graph Isomorphism Network",
    meanRocAuc: 0.761,
    meanPrAuc: 0.347,
    description: "1-WL expressive inductive architecture",
  },
  {
    model: "MPNN",
    name: "Edge-Aware Message Passing",
    meanRocAuc: 0.757,
    meanPrAuc: 0.339,
    description: "Bond-feature aware message passing network",
  },
  {
    model: "RF (Morgan FP)",
    name: "Random Forest Baseline",
    meanRocAuc: 0.732,
    meanPrAuc: 0.350,
    description: "1024-bit Morgan circular fingerprints (radius 2)",
  },
];

export const ENDPOINT_METRICS_DATA: EndpointMetric[] = [
  {
    endpoint: "NR-AR",
    fullTaskName: "Androgen Receptor (Full)",
    ginRocAuc: 0.784,
    rfRocAuc: 0.731,
    gcnRocAuc: 0.721,
    mpnnRocAuc: 0.740,
  },
  {
    endpoint: "NR-AR-LBD",
    fullTaskName: "Androgen Receptor (Ligand Binding)",
    ginRocAuc: 0.820,
    rfRocAuc: 0.878,
    gcnRocAuc: 0.820,
    mpnnRocAuc: 0.857,
  },
  {
    endpoint: "NR-AhR",
    fullTaskName: "Aryl Hydrocarbon Receptor",
    ginRocAuc: 0.865,
    rfRocAuc: 0.821,
    gcnRocAuc: 0.849,
    mpnnRocAuc: 0.856,
  },
  {
    endpoint: "NR-Aromatase",
    fullTaskName: "Aromatase Enzyme Inhibition",
    ginRocAuc: 0.714,
    rfRocAuc: 0.706,
    gcnRocAuc: 0.734,
    mpnnRocAuc: 0.716,
  },
  {
    endpoint: "NR-ER",
    fullTaskName: "Estrogen Receptor Alpha (Full)",
    ginRocAuc: 0.721,
    rfRocAuc: 0.616,
    gcnRocAuc: 0.668,
    mpnnRocAuc: 0.686,
  },
  {
    endpoint: "NR-ER-LBD",
    fullTaskName: "Estrogen Receptor (Ligand Binding)",
    ginRocAuc: 0.719,
    rfRocAuc: 0.763,
    gcnRocAuc: 0.760,
    mpnnRocAuc: 0.737,
  },
  {
    endpoint: "NR-PPAR-gamma",
    fullTaskName: "Peroxisome Proliferator-Activated Receptor",
    ginRocAuc: 0.681,
    rfRocAuc: 0.714,
    gcnRocAuc: 0.749,
    mpnnRocAuc: 0.676,
  },
  {
    endpoint: "SR-ARE",
    fullTaskName: "Antioxidant Response Element",
    ginRocAuc: 0.739,
    rfRocAuc: 0.684,
    gcnRocAuc: 0.727,
    mpnnRocAuc: 0.729,
  },
  {
    endpoint: "SR-ATAD5",
    fullTaskName: "Genotoxicity ATAD5 ATPase",
    ginRocAuc: 0.780,
    rfRocAuc: 0.746,
    gcnRocAuc: 0.782,
    mpnnRocAuc: 0.781,
  },
  {
    endpoint: "SR-HSE",
    fullTaskName: "Heat Shock Response Element",
    ginRocAuc: 0.764,
    rfRocAuc: 0.649,
    gcnRocAuc: 0.745,
    mpnnRocAuc: 0.754,
  },
  {
    endpoint: "SR-MMP",
    fullTaskName: "Mitochondrial Membrane Potential",
    ginRocAuc: 0.793,
    rfRocAuc: 0.770,
    gcnRocAuc: 0.798,
    mpnnRocAuc: 0.797,
  },
  {
    endpoint: "SR-p53",
    fullTaskName: "Tumor Suppressor p53 Activation",
    ginRocAuc: 0.749,
    rfRocAuc: 0.705,
    gcnRocAuc: 0.792,
    mpnnRocAuc: 0.762,
  },
];

export const DDI_RADAR_DATA: DdiRadarMetric[] = [
  {
    metric: "accuracy",
    label: "Test Accuracy",
    gcn: 0.600,
    gin: 0.609,
    fullScale: 1.0,
  },
  {
    metric: "macro_f1",
    label: "Macro-F1",
    gcn: 0.491,
    gin: 0.490,
    fullScale: 1.0,
  },
  {
    metric: "major_recall",
    label: "Major Recall",
    gcn: 0.705,
    gin: 0.609,
    fullScale: 1.0,
  },
  {
    metric: "moderate_f1",
    label: "Moderate F1",
    gcn: 0.686,
    gin: 0.708,
    fullScale: 1.0,
  },
  {
    metric: "minor_f1",
    label: "Minor F1",
    gcn: 0.247,
    gin: 0.262,
    fullScale: 1.0,
  },
];

export const PROOF_STATS = [
  { value: 12, label: "Tox21 endpoints", suffix: "" },
  { value: 7831, label: "Tox21 compounds", suffix: "" },
  { value: 122378, label: "Labelled drug pairs", suffix: "" },
  { value: 3, label: "Severity classes", suffix: "" },
] as const;
