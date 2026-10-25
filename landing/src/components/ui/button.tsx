import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Slot } from "radix-ui";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-[6px] text-sm font-medium tracking-tight whitespace-nowrap transition-colors duration-150 outline-none focus-visible:ring-2 focus-visible:ring-[#2147FF] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default:
          "bg-[#0E1116] text-[#F2F4F7] border border-[#0E1116] hover:bg-[#2147FF] active:translate-y-[1px]",
        signal:
          "bg-[#2147FF] text-[#F2F4F7] border border-[#0E1116] hover:bg-[#0E1116] active:translate-y-[1px]",
        lime:
          "bg-[#D2FF3F] text-[#0E1116] border border-[#0E1116] hover:bg-[#0E1116] hover:text-[#F2F4F7] active:translate-y-[1px] font-semibold",
        outline:
          "bg-transparent text-[#0E1116] border border-[#0E1116] hover:bg-[#0E1116] hover:text-[#F2F4F7] active:translate-y-[1px]",
        ghost:
          "hover:bg-[#0E1116]/10 text-[#0E1116] active:bg-[#0E1116]/20",
        link:
          "text-[#2147FF] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-5 py-2.5",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-7 text-base font-semibold",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ComponentProps<"button">,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : "button";
    return (
      <Comp
        ref={ref as any}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
