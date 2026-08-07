"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, CheckCircle, XCircle } from "lucide-react";
import { couponsApi, type CouponWritePayload } from "@/lib/services";
import type { Coupon } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { formatDate } from "@/lib/utils";
import type { AxiosResponse } from "axios";

interface FormState {
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: string;
  is_active: boolean;
  valid_until: string;
  min_order_value: string;
  usage_limit: string;
}

const empty: FormState = {
  code: "", discount_type: "percentage", discount_value: "",
  is_active: true, valid_until: "", min_order_value: "", usage_limit: "",
};

export default function CouponsPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<FormState>(empty);
  const [editing, setEditing] = useState<Coupon | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    couponsApi.list()
      .then((r: AxiosResponse<Coupon[]>) => setCoupons(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleEdit = (coupon: Coupon) => {
    setEditing(coupon);
    setForm({
      code: coupon.code,
      discount_type: coupon.discount_type,
      discount_value: coupon.discount_value,
      is_active: coupon.is_active,
      valid_until: coupon.valid_until ? coupon.valid_until.slice(0, 10) : "",
      min_order_value: coupon.min_order_value ?? "",
      usage_limit: coupon.usage_limit != null ? String(coupon.usage_limit) : "",
    });
    setError("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty); setError(""); };

  const handleSave = async () => {
    if (!form.code.trim()) { setError("Code is required."); return; }
    if (!form.discount_value || Number(form.discount_value) <= 0) {
      setError("Discount value must be greater than zero.");
      return;
    }
    setSaving(true);
    setError("");
    const payload: CouponWritePayload = {
      code: form.code.trim(),
      discount_type: form.discount_type,
      discount_value: Number(form.discount_value),
      is_active: form.is_active,
      valid_until: form.valid_until ? `${form.valid_until}T23:59:59Z` : null,
      min_order_value: form.min_order_value ? Number(form.min_order_value) : null,
      usage_limit: form.usage_limit ? Number(form.usage_limit) : null,
    };
    try {
      if (editing) {
        await couponsApi.update(editing.id, payload);
      } else {
        await couponsApi.create(payload);
      }
      handleCancel();
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string, string[] | string> } };
      const data = err?.response?.data;
      const firstError = data ? Object.values(data)[0] : null;
      setError((Array.isArray(firstError) ? firstError[0] : firstError) || "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (coupon: Coupon) => {
    if (!confirm(`Delete coupon "${coupon.code}"?`)) return;
    await couponsApi.delete(coupon.id);
    setCoupons((c) => c.filter((x) => x.id !== coupon.id));
  };

  const handleToggleActive = async (coupon: Coupon) => {
    const { data } = await couponsApi.update(coupon.id, { is_active: !coupon.is_active });
    setCoupons((c) => c.map((x) => (x.id === coupon.id ? data : x)));
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Coupons</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-white border border-gray-200 rounded-xl p-5 sticky top-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              {editing ? "Edit coupon" : "New coupon"}
            </h2>
            <div className="space-y-3">
              <Input
                id="code" label="Code *"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="e.g. SAVE10"
              />
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Discount type</label>
                <select
                  value={form.discount_type}
                  onChange={(e) => setForm({ ...form, discount_type: e.target.value as "percentage" | "fixed" })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed amount (£)</option>
                </select>
              </div>
              <Input
                id="discount_value"
                label={form.discount_type === "percentage" ? "Discount (%) *" : "Discount (£) *"}
                type="number" min="0" step="0.01"
                value={form.discount_value}
                onChange={(e) => setForm({ ...form, discount_value: e.target.value })}
              />
              <Input
                id="min_order_value" label="Minimum order value (£, optional)"
                type="number" min="0" step="0.01"
                value={form.min_order_value}
                onChange={(e) => setForm({ ...form, min_order_value: e.target.value })}
              />
              <Input
                id="usage_limit" label="Usage limit (optional)"
                type="number" min="1"
                value={form.usage_limit}
                onChange={(e) => setForm({ ...form, usage_limit: e.target.value })}
                placeholder="Unlimited"
              />
              <Input
                id="valid_until" label="Expires on (optional)"
                type="date"
                value={form.valid_until}
                onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
              />
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">Active</span>
              </label>
              {error && <p className="text-xs text-danger-600">{error}</p>}
              <div className="flex gap-2 pt-1">
                {editing && (
                  <Button variant="outline" size="sm" onClick={handleCancel} className="flex-1">
                    Cancel
                  </Button>
                )}
                <Button size="sm" onClick={handleSave} isLoading={saving} className="flex-1">
                  {editing ? "Save changes" : <><Plus size={13} className="mr-1" />Add coupon</>}
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-sm text-gray-400">Loading…</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      {["Code", "Discount", "Usage", "Expires", "Active", ""].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {coupons.map((coupon) => (
                      <tr key={coupon.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-mono font-medium text-gray-900">{coupon.code}</td>
                        <td className="px-4 py-3 text-gray-600">
                          {coupon.discount_type === "percentage"
                            ? `${coupon.discount_value}%`
                            : `£${coupon.discount_value}`}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {coupon.times_used}{coupon.usage_limit != null ? ` / ${coupon.usage_limit}` : ""}
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {coupon.valid_until ? formatDate(coupon.valid_until) : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <button onClick={() => handleToggleActive(coupon)}>
                            {coupon.is_active
                              ? <CheckCircle size={15} className="text-success-600" />
                              : <XCircle size={15} className="text-gray-300" />}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 justify-end">
                            <button onClick={() => handleEdit(coupon)} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100">
                              <Pencil size={14} />
                            </button>
                            <button onClick={() => handleDelete(coupon)} className="p-1.5 rounded-lg text-gray-400 hover:text-danger-600 hover:bg-danger-50">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!coupons.length && (
                      <tr><td colSpan={6} className="px-4 py-10 text-center text-sm text-gray-400">No coupons yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
