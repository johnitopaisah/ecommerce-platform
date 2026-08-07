"use client";

import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  size?: number;
  className?: string;
}

/** Read-only when onChange is omitted; otherwise an interactive 1-5 picker. */
export default function StarRating({ value, onChange, size = 16, className }: StarRatingProps) {
  const interactive = !!onChange;

  return (
    <div className={cn("flex items-center gap-0.5", className)} role={interactive ? "radiogroup" : undefined}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          disabled={!interactive}
          onClick={() => onChange?.(n)}
          aria-label={interactive ? `Rate ${n} out of 5 stars` : undefined}
          className={cn(!interactive && "cursor-default", interactive && "cursor-pointer")}
        >
          <Star
            size={size}
            className={n <= Math.round(value) ? "fill-star text-star" : "text-gray-300"}
          />
        </button>
      ))}
    </div>
  );
}
