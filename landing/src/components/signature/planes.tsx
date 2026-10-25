import React, { useRef } from "react";
import { motion, useScroll, useTransform, useReducedMotion } from "motion/react";

interface PlaneProps {
  color?: "blue" | "lime" | "ink" | "paper";
  rotate?: number; // -6 to 6 degrees
  className?: string;
  parallaxSpeed?: number; // 0.1 to 0.3
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export const Plane: React.FC<PlaneProps> = ({
  color = "blue",
  rotate = 2,
  className = "",
  parallaxSpeed = 0.15,
  style = {},
  children,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const clampedRotation = Math.max(-6, Math.min(6, rotate));
  const yOffset = useTransform(
    scrollYProgress,
    [0, 1],
    shouldReduceMotion ? [0, 0] : [-50 * parallaxSpeed, 50 * parallaxSpeed]
  );

  const bgColors = {
    blue: "bg-[#2147FF]",
    lime: "bg-[#D2FF3F]",
    ink: "bg-[#0E1116]",
    paper: "bg-[#F2F4F7]",
  };

  return (
    <motion.div
      ref={ref}
      style={{
        y: yOffset,
        rotate: clampedRotation,
        ...style,
      }}
      className={`absolute pointer-events-none select-none ${bgColors[color]} ${className}`}
      aria-hidden="true"
    >
      {children}
    </motion.div>
  );
};
