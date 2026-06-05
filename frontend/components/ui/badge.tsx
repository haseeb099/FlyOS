import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "danger" | "outline";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variant === "default" && "bg-amber-400/15 text-amber-400",
        variant === "success" && "bg-green-500/15 text-green-400",
        variant === "danger" && "bg-red-500/15 text-red-400",
        variant === "outline" && "border border-[#222] text-zinc-400",
        className
      )}
      {...props}
    />
  );
}
