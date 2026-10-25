import React, { useState, useMemo } from "react";
import {
  MEAN_METRICS_DATA,
  PER_ENDPOINT_GIN_RF_DATA,
  DDI_RADAR_DATA,
} from "@/data/metrics.generated";
import { BarChart } from "@/components/charts/bar-chart";
import { Bar } from "@/components/charts/bar";
import { BarXAxis } from "@/components/charts/bar-x-axis";
import { Grid } from "@/components/charts/grid";
import { ChartTooltip } from "@/components/charts/tooltip/chart-tooltip";
import { RadarChart } from "@/components/charts/radar-chart";
import { RadarGrid } from "@/components/charts/radar-grid";
import { RadarAxis } from "@/components/charts/radar-axis";
import { RadarLabels } from "@/components/charts/radar-labels";
import { RadarArea } from "@/components/charts/radar-area";
import type { RadarData, RadarMetric } from "@/components/charts/radar-context";

function ChartUnavailable() {
  console.error("Chart data unavailable: dataset is missing or empty.");
  return (
    <div
      role="alert"
      className="w-full min-w-0 h-[320px] flex items-center justify-center border-2 border-dashed border-[#0E1116]/30 rounded-[8px] bg-[#FFFFFF] text-sm font-mono text-[#0E1116]/70"
    >
      Chart data unavailable
    </div>
  );
}

export const PerformanceSection: React.FC = () => {
  const [activeChartTab, setActiveChartTab] = useState<"mean" | "endpoints" | "ddi">("mean");

  // Dynamically prepare radar series & metric keys from generated DDI data
  const { radarSeries, radarMetrics } = useMemo(() => {
    if (!DDI_RADAR_DATA || DDI_RADAR_DATA.length === 0) {
      return { radarSeries: [], radarMetrics: [] };
    }

    const gcnVals: Record<string, number> = {};
    const ginVals: Record<string, number> = {};

    const metrics: RadarMetric[] = DDI_RADAR_DATA.map((d) => {
      const key = d.metric.toLowerCase().replace(/[^a-z0-9]/g, "");
      gcnVals[key] = Math.round(d.GCN * 1000) / 10;
      ginVals[key] = Math.round(d.GIN * 1000) / 10;
      return { key, label: d.metric };
    });

    const series: RadarData[] = [
      { label: "GCN Dual-Encoder", color: "#2147FF", values: gcnVals },
      { label: "GIN Dual-Encoder", color: "#D2FF3F", values: ginVals },
    ];

    return { radarSeries: series, radarMetrics: metrics };
  }, []);

  return (
    <section
      id="performance"
      className="relative bg-[#FFFFFF] text-[#0E1116] py-20 md:py-32 border-b border-[#0E1116] scroll-mt-16"
    >
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
        {/* Section Header */}
        <div className="max-w-[62ch] mb-12 md:mb-16">
          <h2 className="text-[#0E1116] mb-4">
            What the numbers say, and what they don't.
          </h2>
          <p className="text-lg md:text-[19px] text-[#0E1116]/80 leading-relaxed">
            Rigorous benchmark evaluation across 12 Tox21 bioassays and thousands of unseen drug pairs.
            GNN architectures demonstrate superior structural generalization over circular fingerprints,
            though high class imbalance in clinical interactions demands calibrated appraisal.
          </p>
        </div>

        {/* Tab Controls for Detailed Charts */}
        <div className="flex flex-wrap items-center gap-2 mb-8 border-b border-[#0E1116] pb-4">
          <button
            type="button"
            onClick={() => setActiveChartTab("mean")}
            className={`px-4 py-2 rounded-[6px] border font-mono text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
              activeChartTab === "mean"
                ? "bg-[#0E1116] text-[#F2F4F7] border-[#0E1116]"
                : "bg-[#F2F4F7] text-[#0E1116] border-[#0E1116]/40 hover:bg-[#0E1116]/10"
            }`}
          >
            (a) Mean ROC-AUC by Model
          </button>
          <button
            type="button"
            onClick={() => setActiveChartTab("endpoints")}
            className={`px-4 py-2 rounded-[6px] border font-mono text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
              activeChartTab === "endpoints"
                ? "bg-[#0E1116] text-[#F2F4F7] border-[#0E1116]"
                : "bg-[#F2F4F7] text-[#0E1116] border-[#0E1116]/40 hover:bg-[#0E1116]/10"
            }`}
          >
            (b) Per-Endpoint: GIN vs Random Forest
          </button>
          <button
            type="button"
            onClick={() => setActiveChartTab("ddi")}
            className={`px-4 py-2 rounded-[6px] border font-mono text-xs sm:text-sm font-bold transition-colors cursor-pointer ${
              activeChartTab === "ddi"
                ? "bg-[#0E1116] text-[#F2F4F7] border-[#0E1116]"
                : "bg-[#F2F4F7] text-[#0E1116] border-[#0E1116]/40 hover:bg-[#0E1116]/10"
            }`}
          >
            (c) Interaction Radar: GCN vs GIN
          </button>
        </div>

        {/* Chart View Container */}
        <div className="bg-[#F2F4F7] border border-[#0E1116] rounded-[12px] p-6 md:p-8 mb-8 min-w-0">
          {/* TAB A: Mean ROC-AUC per model (4 bars) */}
          {activeChartTab === "mean" && (
            <div className="min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 pb-4 border-b border-[#0E1116]/20">
                <div>
                  <h3 className="text-xl font-bold text-[#0E1116]">
                    Mean ROC-AUC over 12 Tox21 Endpoints
                  </h3>
                  <p className="text-xs font-mono text-[#0E1116]/70 mt-1">
                    Evaluated on Bemis-Murcko scaffold split test sets
                  </p>
                </div>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-[#2147FF] border border-[#0E1116] inline-block" />
                    Mean ROC-AUC
                  </span>
                </div>
              </div>

              {!MEAN_METRICS_DATA || MEAN_METRICS_DATA.length === 0 ? (
                <ChartUnavailable />
              ) : (
                <div className="w-full min-w-0 h-[340px]">
                  <BarChart
                    data={MEAN_METRICS_DATA as unknown as Record<string, unknown>[]}
                    xDataKey="model"
                    className="w-full h-full min-w-0"
                    barGap={0.35}
                  >
                    <Grid horizontal vertical={false} />
                    <BarXAxis showAllLabels />
                    <ChartTooltip showDatePill={false} />
                    <Bar dataKey="meanRocAuc" fill="#2147FF" stroke="#0E1116" />
                  </BarChart>
                </div>
              )}

              <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono pt-4 border-t border-[#0E1116]/20">
                {MEAN_METRICS_DATA.map((m) => (
                  <div key={m.model} className="p-2.5 bg-[#FFFFFF] border border-[#0E1116]/30 rounded-[6px]">
                    <span className="block text-[#0E1116]/60 text-[10px]">{m.model}</span>
                    <span className="text-base font-bold text-[#0E1116]">{m.meanRocAuc.toFixed(3)}</span>
                    <span className="block text-[10px] text-[#0E1116]/70">PR: {m.meanPrAuc.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB B: Per-Endpoint ROC-AUC, GIN vs Random Forest (24 bars) */}
          {activeChartTab === "endpoints" && (
            <div className="min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 pb-4 border-b border-[#0E1116]/20">
                <div>
                  <h3 className="text-xl font-bold text-[#0E1116]">
                    Per-Endpoint ROC-AUC: GIN vs Random Forest Baseline
                  </h3>
                  <p className="text-xs font-mono text-[#0E1116]/70 mt-1">
                    GIN wins on 9 of 12 endpoints under the scaffold split
                  </p>
                </div>
                <div className="flex items-center gap-4 font-mono text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-[#2147FF] border border-[#0E1116] inline-block" />
                    GIN (GNN)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-[#0E1116] border border-[#0E1116] inline-block" />
                    Random Forest (Fingerprint)
                  </span>
                </div>
              </div>

              {!PER_ENDPOINT_GIN_RF_DATA || PER_ENDPOINT_GIN_RF_DATA.length === 0 ? (
                <ChartUnavailable />
              ) : (
                <div className="w-full min-w-0 h-[340px] overflow-x-auto">
                  <div className="min-w-[680px] h-full min-w-0">
                    <BarChart
                      data={PER_ENDPOINT_GIN_RF_DATA as unknown as Record<string, unknown>[]}
                      xDataKey="endpoint"
                      className="w-full h-full min-w-0"
                      barGap={0.2}
                    >
                      <Grid horizontal vertical={false} />
                      <BarXAxis showAllLabels />
                      <ChartTooltip showDatePill={false} />
                      <Bar dataKey="GIN" fill="#2147FF" stroke="#0E1116" groupGap={4} />
                      <Bar dataKey="RF" fill="#0E1116" stroke="#0E1116" groupGap={4} />
                    </BarChart>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB C: Radar Chart for GCN vs GIN interaction metrics (2 polygons) */}
          {activeChartTab === "ddi" && (
            <div className="min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 pb-4 border-b border-[#0E1116]/20">
                <div>
                  <h3 className="text-xl font-bold text-[#0E1116]">
                    Interaction Benchmark Radar: GCN vs GIN
                  </h3>
                  <p className="text-xs font-mono text-[#0E1116]/70 mt-1">
                    Multi-class severity performance on cold-start unseen drug pairs
                  </p>
                </div>
                <div className="flex items-center gap-4 font-mono text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-[#2147FF] border border-[#0E1116] inline-block" />
                    GCN Dual-Encoder
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 bg-[#D2FF3F] border border-[#0E1116] inline-block text-[#0E1116]" />
                    GIN Dual-Encoder
                  </span>
                </div>
              </div>

              {radarSeries.length === 0 ? (
                <ChartUnavailable />
              ) : (
                <div className="w-full min-w-0 h-[360px] flex items-center justify-center">
                  <RadarChart
                    size={340}
                    data={radarSeries}
                    metrics={radarMetrics}
                    className="w-full h-full min-w-0 flex items-center justify-center"
                  >
                    <RadarGrid />
                    <RadarAxis />
                    <RadarLabels />
                    <RadarArea index={0} color="#2147FF" showPoints />
                    <RadarArea index={1} color="#D2FF3F" showPoints />
                  </RadarChart>
                </div>
              )}

              <div className="mt-4 p-3 bg-[#FFFFFF] border border-[#0E1116]/30 rounded-[6px] text-xs font-mono leading-relaxed text-[#0E1116]/80">
                <strong>Cold-Start Split Metrics:</strong> Test accuracy GCN 0.600, GIN 0.609; macro-F1 GCN 0.491, GIN 0.490; Major-class recall GCN 0.705, GIN 0.609. The Minor class is the weakest due to support scarcity (67 instances in DDInter cold-start split).
              </div>
            </div>
          )}
        </div>

        {/* Unconditionally rendered screen-reader accessible tables for all 3 charts */}
        <div className="sr-only">
          {/* Accessible Table for Chart A */}
          <table>
            <caption>Mean ROC-AUC performance per model on Tox21 scaffold split</caption>
            <thead>
              <tr>
                <th scope="col">Model Architecture</th>
                <th scope="col">Mean ROC-AUC</th>
                <th scope="col">Mean PR-AUC</th>
              </tr>
            </thead>
            <tbody>
              {MEAN_METRICS_DATA.map((row) => (
                <tr key={row.model}>
                  <td>{row.model}</td>
                  <td>{row.meanRocAuc.toFixed(3)}</td>
                  <td>{row.meanPrAuc.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Accessible Table for Chart B */}
          <table>
            <caption>Per-endpoint ROC-AUC comparison between GIN and Random Forest on 12 Tox21 assays</caption>
            <thead>
              <tr>
                <th scope="col">Assay Endpoint</th>
                <th scope="col">GIN ROC-AUC</th>
                <th scope="col">Random Forest ROC-AUC</th>
              </tr>
            </thead>
            <tbody>
              {PER_ENDPOINT_GIN_RF_DATA.map((row) => (
                <tr key={row.endpoint}>
                  <td>{row.endpoint}</td>
                  <td>{row.GIN.toFixed(3)}</td>
                  <td>{row.RF.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Accessible Table for Chart C */}
          <table>
            <caption>DDI benchmark radar metrics comparing GCN and GIN on cold-start test split</caption>
            <thead>
              <tr>
                <th scope="col">Metric</th>
                <th scope="col">GCN Score</th>
                <th scope="col">GIN Score</th>
              </tr>
            </thead>
            <tbody>
              {DDI_RADAR_DATA.map((row) => (
                <tr key={row.metric}>
                  <td>{row.label}</td>
                  <td>{row.GCN.toFixed(3)}</td>
                  <td>{row.GIN.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Strict Mandatory Caption */}
        <p className="font-mono text-xs md:text-sm text-[#0E1116]/75 border-l-2 border-[#2147FF] pl-3 py-1">
          Single run per model. Toxicity uses a scaffold split; interactions use a cold-start split on unseen drugs.
        </p>
      </div>
    </section>
  );
};
