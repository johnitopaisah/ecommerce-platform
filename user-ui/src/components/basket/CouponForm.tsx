"use client";

import { useState } from "react";
import { Tag, X } from "lucide-react";
import { useBasketStore } from "@/store/basketStore";
import { Button } from "@/components/ui/Button";

export default function CouponForm() {
  const { basket, applyCoupon, removeCoupon, couponLoading } = useBasketStore();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return;
    const err = await applyCoupon(code.trim());
    setError(err);
    if (!err) setCode("");
  };

  if (basket.coupon_code) {
    return (
      <div className="flex items-center justify-between bg-success-50 border border-green-200 rounded-lg px-3 py-2 text-sm">
        <span className="flex items-center gap-1.5 text-success-700 font-medium">
          <Tag size={13} />
          {basket.coupon_code} applied
        </span>
        <button
          onClick={() => removeCoupon()}
          disabled={couponLoading}
          aria-label="Remove coupon"
          className="text-gray-400 hover:text-gray-700"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleApply} className="space-y-1.5">
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => { setCode(e.target.value); setError(null); }}
          placeholder="Coupon code"
          className="flex-1 min-w-0 border border-gray-300 rounded-lg px-3 py-1.5 text-sm uppercase placeholder:normal-case"
        />
        <Button type="submit" size="sm" variant="secondary" isLoading={couponLoading} disabled={!code.trim()}>
          Apply
        </Button>
      </div>
      {error && <p className="text-xs text-danger-600">{error}</p>}
    </form>
  );
}
