import React, { useState } from "react";
import { motion, useReducedMotion } from "motion/react";

export interface RadarSeriesConfig {
  key: string;
  label: string;
  color: string;
  fillColor?: string;
}

export interface RadarMetric {
  metric: string;
  label: string;
  fullScale?: number;
  [key: string]: any;
}

export interface RadarChartProps {
  data: RadarMetric[];
  series: RadarSeriesConfig[];
  size?: number;
  className?: string;
}

export const RadarChart: React.FC<RadarChartProps> = ({
  data,
  series,
  size = 380,
  className = "",
}) => {
  const [hoveredMetric, setHoveredMetric] = useState<number | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const center = size / 2;
  const radius = size * 0.38;
  const totalAxes = data.length;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Grid levels (25%, 50%, 75%, 100%)
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  // Helper to calculate (x, y) given radius and axis index
  const getCoordinates = (r: number, index: number) => {
    // Start from top (-PI / 2)
    const angle = index * angleStep - Math.PI / 2;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  // Generate path string for polygon given values
  const getPolygonPath = (seriesKey: string, scaleFactor = 1) => {
    const points = data.map((d, i) => {
      const val = Number(d[seriesKey] ?? 0);
      const maxVal = d.fullScale || 1.0;
      const normalized = Math.max(0, Math.min(1, val / maxVal)) * scaleFactor;
      const coord = getCoordinates(normalized * radius, i);
      return `${coord.x},${coord.y}`;
    });
    return `M ${points.join(" L ")} Z`;
  };

  return (
    <div className={`relative flex flex-col items-center justify-center font-mono ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="overflow-visible select-none"
        aria-hidden="true"
      >
        {/* Concentric Grid Polygons */}
        {gridLevels.map((lvl, lvlIdx) => {
          const gridPoints = Array.from({ length: totalAxes }, (_, i) => {
            const coord = getCoordinates(radius * lvl, i);
            return `${coord.x},${coord.y}`;
          }).join(" L ");

          return (
            <g key={lvlIdx}>
              <polygon
                points={gridPoints}
                fill="none"
                stroke="#0E1116"
                strokeOpacity={0.15}
                strokeWidth={1}
                strokeDasharray={lvlIdx < 3 ? "3 3" : undefined}
              />
              {/* Level indicator */}
              <text
                x={center + 4}
                y={center - radius * lvl + 10}
                className="text-[9px] fill-[#0E1116]/60 font-mono"
              >
                {(lvl * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}

        {/* Axes Lines and Labels */}
        {data.map((d, i) => {
          const outer = getCoordinates(radius, i);
          const labelCoord = getCoordinates(radius + 26, i);

          let textAnchor: "inherit" | "end" | "start" | "middle" = "middle";
          if (labelCoord.x > center + 10) textAnchor = "start";
          else if (labelCoord.x < center - 10) textAnchor = "end";

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredMetric(i)}
              onMouseLeave={() => setHoveredMetric(null)}
              className="cursor-pointer"
            >
              <line
                x1={center}
                y1={center}
                x2={outer.x}
                y2={outer.y}
                stroke="#0E1116"
                strokeOpacity={0.2}
                strokeWidth={1}
              />
              <text
                x={labelCoord.x}
                y={labelCoord.y + 4}
                textAnchor={textAnchor}
                className={`text-[11px] font-mono transition-colors duration-150 ${
                  hoveredMetric === i
                    ? "fill-[#2147FF] font-bold"
                    : "fill-[#0E1116] font-medium"
                }`}
              >
                {d.label}
              </text>
            </g>
          );
        })}

        {/* Series Polygons */}
        {series.map((s, seriesIdx) => {
          const path = getPolygonPath(s.key);
          const zeroPath = getPolygonPath(s.key, 0.05);

          return (
            <g key={s.key}>
              <motion.path
                d={shouldReduceMotion ? path : path}
                initial={shouldReduceMotion ? { opacity: 0.8 } : { d: zeroPath, opacity: 0 }}
                animate={{ d: path, opacity: 0.7 }}
                transition={{
                  duration: 0.8,
                  delay: seriesIdx * 0.15,
                  ease: [0.16, 1, 0.3, 1],
                }}
                fill={s.fillColor || s.color}
                fillOpacity={0.25}
                stroke={s.color}
                strokeWidth={2}
              />
              {/* Data points */}
              {data.map((d, i) => {
                const val = Number(d[s.key] ?? 0);
                const maxVal = d.fullScale || 1.0;
                const normalized = Math.max(0, Math.min(1, val / maxVal));
                const coord = getCoordinates(normalized * radius, i);

                return (
                  <circle
                    key={i}
                    cx={coord.x}
                    cy={coord.y}
                    r={hoveredMetric === i ? 5 : 3.5}
                    fill={s.color}
                    stroke="#0E1116"
                    strokeWidth={1.5}
                  />
                );
              })}
            </g>
          );
        })}
      </svg>

      {/* Tooltip on hover */}
      {hoveredMetric !== null && (
        <div className="absolute bottom-2 bg-[#0E1116] text-[#F2F4F7] px-3 py-2 rounded-[6px] border border-[#0E1116] text-xs pointer-events-none z-10">
          <div className="font-bold text-[#D2FF3F] mb-1">
            {data[hoveredMetric].label}
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
                {Number(data[hoveredMetric][s.key]).toFixed(3)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
