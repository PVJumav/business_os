import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

const variantClasses: Record<string, string> = {
  primary: "bg-[var(--brand)] text-white shadow-sm hover:bg-[var(--brand-strong)]",
  secondary: "border border-[var(--line)] bg-white/85 text-slate-800 shadow-sm hover:bg-[var(--brand-soft)]",
  ghost: "text-slate-600 hover:bg-[var(--brand-soft)] hover:text-[var(--brand-strong)]",
  danger: "bg-red-600 text-white shadow-sm shadow-red-900/20 hover:bg-red-700",
};

const sizeClasses: Record<string, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-base",
};

export default function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`focus-ring inline-flex items-center gap-2 rounded-lg font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
