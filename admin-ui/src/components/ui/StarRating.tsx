import { Star } from "lucide-react";

/** Read-only star display — admin-ui only ever shows ratings, never collects them. */
export default function StarRating({ value, size = 14 }: { value: number; size?: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} size={size} className={n <= Math.round(value) ? "fill-star text-star" : "text-gray-300"} />
      ))}
    </div>
  );
}
