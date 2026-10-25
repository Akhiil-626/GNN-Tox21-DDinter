import React, { useState } from "react";
import { motion, useReducedMotion } from "motion/react";

export interface BarSeriesConfig {
  key: string;
  label: string;
  color: string;
}

export interface BarChartProps {
  data: Array<Record<string, any>>;
  xDataKey: string;
  series: BarSeriesConfig[];
  yDomain?: [number, number];
  height?: number;
  className?: string;
  formatY?: (val: number) => string;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  xDataKey,
  series,
  yDomain = [0, 1],
  height = 320,
  className = "",
  formatY = (v) => v.toFixed(3),
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const [minY, maxY] = yDomain;
  const padding = { top: 24, right: 24, bottom: 44, left: 54 };

  const yTicks = [minY, (minY + maxY) / 2, maxY];

  return (
    <div className={`relative w-full overflow-hidden select-none font-mono ${className}`}>
      <svg
        viewBox={`0 0 700 ${height}`}
        className="w-full h-auto overflow-visible"
        aria-hidden="true"
      >
        {/* Y Axis Grid Lines */}
        {yTicks.map((tick, i) => {
          const norm = (tick - minY) / (maxY - minY);
          const y = height - padding.bottom - norm * (height - padding.top - padding.bottom);
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={y}
                x2={700 - padding.right}
                y2={y}
                stroke="#0E1116"
                strokeOpacity={0.12}
                strokeDasharray="4 4"
                strokeWidth={1}
              />
              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                className="text-[11px] fill-[#0E1116]/70 font-mono"
              >
                {formatY(tick)}
              </text>
            </g>
          );
        })}

        {/* X Axis Baseline */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={700 - padding.right}
          y2={height - padding.bottom}
          stroke="#0E1116"
          strokeWidth={1.5}
        />

        {/* Bars */}
        {data.map((item, itemIdx) => {
          const groupWidth = (700 - padding.left - padding.right) / data.length;
          const groupX = padding.left + itemIdx * groupWidth;
          const barWidth = Math.min(28, (groupWidth * 0.75) / series.length);
          const innerOffset = (groupWidth - barWidth * series.length) / 2;

          return (
            <g
              key={itemIdx}
              onMouseEnter={() => setHoveredIdx(itemIdx)}
              onMouseLeave={() => setHoveredIdx(null)}
              className="cursor-pointer"
            >
              {/* Hover column backdrop */}
              {hoveredIdx === itemIdx && (
                <rect
                  x={groupX + 2}
                  y={padding.top}
                  width={groupWidth - 4}
                  height={height - padding.top - padding.bottom}
                  fill="#0E1116"
                  fillOpacity={0.04}
                  rx={4}
                />
              )}

              {series.map((s, seriesIdx) => {
                const val = Number(item[s.key] ?? 0);
                const normVal = Math.max(0, Math.min(1, (val - minY) / (maxY - minY)));
                const barHeight = normVal * (height - padding.top - padding.bottom);
                const barX = groupX + innerOffset + seriesIdx * barWidth;
                const barY = height - padding.bottom - barHeight;

                return (
                  <motion.rect
                    key={s.key}
                    x={barX}
                    y={shouldReduceMotion ? barY : height - padding.bottom}
                    width={Math.max(4, barWidth - 3)}
                    height={shouldReduceMotion ? barHeight : 0}
                    animate={{
                      y: barY,
                      height: barHeight,
                    }}
                    transition={{
                      duration: 0.6,
                      delay: itemIdx * 0.04 + seriesIdx * 0.08,
                      ease: [0.16, 1, 0.3, 1],
                    }}
                    fill={s.color}
                    stroke="#0E1116"
                    strokeWidth={1}
                    rx={2}
                  />
                );
              })}

              {/* X Axis Label */}
              <text
                x={groupX + groupWidth / 2}
                y={height - padding.bottom + 18}
                textAnchor="middle"
                className="text-[11px] font-mono fill-[#0E1116] font-medium"
              >
                {String(item[xDataKey])}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {hoveredIdx !== null && (
        <div
          className="absolute top-2 right-4 bg-[#0E1116] text-[#F2F4F7] px-3 py-2 rounded-[6px] border border-[#0E1116] text-xs pointer-events-none shadow-none z-10"
        >
          <div className="font-bold text-[#D2FF3F] mb-1">
            {data[hoveredIdx][xDataKey]}
          </div>
          {series.map((s) => (
            <div key={s.key} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5 text-paper/80">
                <span
                  className="w-2.5 h-2.5 rounded-sm inline-block"
                  style={{ backgroundColor: s.color }}
                />
                {s.label}:
              </span>
              <span className="font-mono font-bold text-white">
                {formatY(Number(data[hoveredIdx][s.key]))}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
