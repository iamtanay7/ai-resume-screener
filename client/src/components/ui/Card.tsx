import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = "", hover = false }: CardProps) {
  return (
    <div
      className={[
        "rounded-xl border border-neutral-200 bg-white p-6 shadow-sm",
        hover
          ? "transition-shadow duration-200 hover:shadow-md cursor-pointer"
          : "",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}
