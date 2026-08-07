import { Check, Clock, XCircle, RotateCcw } from "lucide-react";
import type { OrderStatus } from "@/types";

const STEPS: { status: OrderStatus; label: string }[] = [
  { status: "confirmed", label: "Confirmed" },
  { status: "processing", label: "Processing" },
  { status: "shipped", label: "Shipped" },
  { status: "delivered", label: "Delivered" },
];

interface Props {
  status: OrderStatus;
}

export default function OrderStatusTimeline({ status }: Props) {
  if (status === "cancelled" || status === "refunded") {
    const isCancelled = status === "cancelled";
    return (
      <div className="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded-xl px-5 py-4">
        {isCancelled ? (
          <XCircle size={20} className="text-red-500 shrink-0" />
        ) : (
          <RotateCcw size={20} className="text-gray-500 shrink-0" />
        )}
        <p className="text-sm text-gray-600">
          {isCancelled ? "This order was cancelled." : "This order was refunded."}
        </p>
      </div>
    );
  }

  // Pending sits before the tracked timeline — nothing has been confirmed yet.
  const currentIndex = status === "pending" ? -1 : STEPS.findIndex((s) => s.status === status);

  return (
    <div className="flex items-start">
      {STEPS.map((step, i) => {
        const done = i <= currentIndex;
        const isLast = i === STEPS.length - 1;
        return (
          <div key={step.status} className={`flex items-center ${isLast ? "" : "flex-1"}`}>
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  done ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-400"
                }`}
              >
                {done ? <Check size={15} /> : <Clock size={14} />}
              </div>
              <span className={`text-xs font-medium ${done ? "text-gray-900" : "text-gray-400"}`}>
                {step.label}
              </span>
            </div>
            {!isLast && (
              <div className={`flex-1 h-0.5 mx-2 mb-5 ${i < currentIndex ? "bg-gray-900" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
