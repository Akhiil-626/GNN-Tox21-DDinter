import React, { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";

interface TextRevealProps {
  lines: string[];
  className?: string;
  as?: "h1" | "h2" | "h3" | "div";
}

export const TextReveal: React.FC<TextRevealProps> = ({
  lines,
  className = "",
  as = "h2",
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-10%" });
  const shouldReduceMotion = useReducedMotion();

  const Component = as;

  return (
    <Component ref={ref as any} className={`overflow-hidden ${className}`}>
      {lines.map((line, index) => (
        <span key={index} className="block overflow-hidden py-0.5">
          <motion.span
            className="block"
            initial={shouldReduceMotion ? { y: 0, opacity: 1 } : { y: "100%", opacity: 0 }}
            animate={
              isInView || shouldReduceMotion
                ? { y: "0%", opacity: 1 }
                : { y: "100%", opacity: 0 }
            }
            transition={{
              duration: 0.7,
              delay: index * 0.08,
              ease: [0.16, 1, 0.3, 1], // exact specified cubic-bezier
            }}
          >
            {line}
          </motion.span>
        </span>
      ))}
    </Component>
  );
};
