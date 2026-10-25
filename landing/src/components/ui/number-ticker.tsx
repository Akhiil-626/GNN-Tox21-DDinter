import React, { useEffect, useRef, useState } from "react";
import { useInView, useReducedMotion } from "motion/react";

interface NumberTickerProps {
  value: number;
  direction?: "up" | "down";
  delay?: number;
  className?: string;
  formatNumber?: boolean;
}

export const NumberTicker: React.FC<NumberTickerProps> = ({
  value,
  direction = "up",
  delay = 0,
  className = "",
  formatNumber = true,
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  // Trigger once at 40% in view as specified
  const isInView = useInView(ref, { once: true, amount: 0.4 });
  const shouldReduceMotion = useReducedMotion();
  const [displayValue, setDisplayValue] = useState(
    shouldReduceMotion ? value : direction === "down" ? value : 0
  );

  useEffect(() => {
    if (shouldReduceMotion) {
      setDisplayValue(value);
      return;
    }

    if (!isInView) return;

    let start = direction === "down" ? value : 0;
    const end = value;
    const duration = 1600; // ms
    const startTime = performance.now() + delay * 1000;

    let animationFrameId: number;

    const updateCounter = (currentTime: number) => {
      if (currentTime < startTime) {
        animationFrameId = requestAnimationFrame(updateCounter);
        return;
      }

      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = Math.floor(start + (end - start) * easeProgress);

      setDisplayValue(current);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(updateCounter);
      } else {
        setDisplayValue(end);
      }
    };

    animationFrameId = requestAnimationFrame(updateCounter);
    return () => cancelAnimationFrame(animationFrameId);
  }, [isInView, value, direction, delay, shouldReduceMotion]);

  const finalFormatted = formatNumber
    ? new Intl.NumberFormat("en-US").format(value)
    : value.toString();

  const formatted = formatNumber
    ? new Intl.NumberFormat("en-US").format(displayValue)
    : displayValue.toString();

  return (
    <span ref={ref} className={`tabular-nums font-mono ${className}`}>
      <span className="sr-only">{finalFormatted}</span>
      <span aria-hidden="true">{formatted}</span>
    </span>
  );
};
