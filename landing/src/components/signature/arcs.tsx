import React, { useRef } from "react";
import { motion, useScroll, useTransform, useInView, useReducedMotion } from "motion/react";

interface ArcSetProps {
  color?: "blue" | "lime" | "ink";
  baseRadius?: number; // 280 - 720
  gap?: number;
  rotationDuration?: number; // 20 - 40s
  className?: string;
  clockwise?: boolean;
}

export const ArcSet: React.FC<ArcSetProps> = ({
  color = "lime",
  baseRadius = 380,
  gap = 48,
  rotationDuration = 32,
  className = "",
  clockwise = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { margin: "100px" });
  const shouldReduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  const pathDraw = useTransform(scrollYProgress, [0, 0.7], [0.1, 1]);

  const strokeColors = {
    blue: "#2147FF",
    lime: "#D2FF3F",
    ink: "#0E1116",
  };

  const strokeColor = strokeColors[color];
  const maxRadius = baseRadius + gap * 2;
  const viewBoxSize = (maxRadius + 20) * 2;
  const center = viewBoxSize / 2;

  const radii = [baseRadius, baseRadius + gap, baseRadius + gap * 2];

  return (
    <div
      ref={containerRef}
      className={`absolute pointer-events-none select-none overflow-visible ${className}`}
      aria-hidden="true"
    >
      <motion.svg
        width={viewBoxSize}
        height={viewBoxSize}
        viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        animate={
          isInView && !shouldReduceMotion
            ? { rotate: clockwise ? 360 : -360 }
            : { rotate: 0 }
        }
        transition={{
          repeat: Infinity,
          ease: "linear",
          duration: rotationDuration,
        }}
        style={{ transformOrigin: "center center" }}
      >
        {radii.map((r, i) => {
          const circumference = 2 * Math.PI * r;
          // Dash array create interrupted crisp arcs
          const dashLength = circumference * 0.75;
          return (
            <motion.circle
              key={i}
              cx={center}
              cy={center}
              r={r}
              stroke={strokeColor}
              strokeWidth="2"
              strokeDasharray={`${dashLength} ${circumference - dashLength}`}
              strokeLinecap="round"
              style={{
                pathLength: shouldReduceMotion ? 1 : pathDraw,
                opacity: 0.9,
              }}
            />
          );
        })}
      </motion.svg>
    </div>
  );
};
