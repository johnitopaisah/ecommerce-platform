"use client";

import { CheckCircle2, XCircle, Info, X } from "lucide-react";
import { useToastStore, type ToastType } from "@/store/toastStore";
import { cn } from "@/lib/utils";

const STYLES: Record<ToastType, { icon: typeof CheckCircle2; classes: string }> = {
  success: { icon: CheckCircle2, classes: "bg-success-50 text-success-700 border-success-600/20" },
  error: { icon: XCircle, classes: "bg-danger-50 text-danger-700 border-danger-600/20" },
  info: { icon: Info, classes: "bg-info-50 text-info-700 border-info-600/20" },
};

export default function Toaster() {
  const { toasts, dismiss } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => {
        const { icon: Icon, classes } = STYLES[toast.type];
        return (
          <div
            key={toast.id}
            role="status"
            className={cn(
              "flex items-start gap-2.5 rounded-lg border px-4 py-3 shadow-lg text-sm",
              classes
            )}
          >
            <Icon size={18} className="shrink-0 mt-0.5" />
            <p className="flex-1">{toast.message}</p>
            <button onClick={() => dismiss(toast.id)} className="shrink-0 opacity-60 hover:opacity-100">
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
