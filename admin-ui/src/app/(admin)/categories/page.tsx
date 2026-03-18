"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, CheckCircle, XCircle } from "lucide-react";
import { categoriesApi } from "@/lib/services";
import type { Category } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

interface FormState { name: string; description: string; is_active: boolean; }
const empty: FormState = { name: "", description: "", is_active: true };

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<FormState>(empty);
  const [editing, setEditing] = useState<Category | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    categoriesApi.list()
      .then((r) => setCategories(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleEdit = (cat: Category) => {
    setEditing(cat);
    setForm({ name: cat.name, description: cat.description, is_active: cat.is_active });
    setError("");
  };

  const handleCancel = () => { setEditing(null); setForm(empty); setError(""); };

  const handleSave = async () => {
    if (!form.name.trim()) { setError("Name is required."); return; }
    setSaving(true);
    try {
      if (editing) {
        await categoriesApi.update(editing.slug, form);
      } else {
        await categoriesApi.create(form);
      }
      handleCancel();
      load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (slug: string) => {
    if (!confirm("Delete this category? Products in it will be unlinked.")) return;
    await categoriesApi.delete(slug);
    setCategories((c) => c.filter((x) => x.slug !== slug));
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Categories</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form */}
        <div className="lg:col-span-1">
          <div className="bg-white border border-gray-200 rounded-xl p-5 sticky top-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              {editing ? "Edit category" : "New category"}
            </h2>
            <div className="space-y-3">
              <Input
                id="name" label="Name *"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Electronics"
              />
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">Active</span>
              </label>
              {error && <p className="text-xs text-red-500">{error}</p>}
              <div className="flex gap-2 pt-1">
                {editing && (
                  <Button variant="outline" size="sm" onClick={handleCancel} className="flex-1">
                    Cancel
                  </Button>
                )}
                <Button size="sm" onClick={handleSave} isLoading={saving} className="flex-1">
                  {editing ? "Save changes" : <><Plus size={13} className="mr-1" />Add category</>}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-sm text-gray-400">Loading…</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    {["Name", "Products", "Active", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {categories.map((cat) => (
                    <tr key={cat.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{cat.name}</p>
                        <p className="text-xs text-gray-400">{cat.slug}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{cat.product_count}</td>
                      <td className="px-4 py-3">
                        {cat.is_active
                          ? <CheckCircle size={15} className="text-green-500" />
                          : <XCircle size={15} className="text-gray-300" />}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 justify-end">
                          <button
                            onClick={() => handleEdit(cat)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(cat.slug)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!categories.length && (
                    <tr>
                      <td colSpan={4} className="px-4 py-10 text-center text-sm text-gray-400">No categories yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
