"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import { rolesApi } from "@/lib/services";
import { usePermissionsStore } from "@/store/permissionsStore";
import type { Role, Permission } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import RoleBadge from "@/components/rbac/RoleBadge";
import { extractApiError } from "@/lib/utils";

interface FormState {
  name: string;
  codenames: Set<string>;
}

export default function RolesPage() {
  const { hasPermission, permissions: myPermissions, isSuperuser } = usePermissionsStore();
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Role | null>(null);
  const [form, setForm] = useState<FormState>({ name: "", codenames: new Set() });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const canManageRoles = hasPermission("rbac.manage_roles");

  const load = () => {
    setLoading(true);
    Promise.all([rolesApi.list(), rolesApi.permissions()])
      .then(([rolesRes, permsRes]) => {
        setRoles(rolesRes.data);
        setAllPermissions(permsRes.data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // Grouped by domain (app_label) — this isn't an arbitrary UI choice, it's
  // the same grouping the backend's permission model already has (each
  // custom permission lives in Meta.permissions on a specific app's model).
  const groupedPermissions = useMemo(() => {
    const groups: Record<string, Permission[]> = {};
    for (const p of allPermissions) {
      if (!isSuperuser && !myPermissions.includes(p.codename_full)) continue;
      (groups[p.app_label] ??= []).push(p);
    }
    return groups;
  }, [allPermissions, myPermissions, isSuperuser]);

  const openCreate = () => {
    setEditing(null);
    setForm({ name: "", codenames: new Set() });
    setError("");
  };

  const openEdit = (role: Role) => {
    setEditing(role);
    setForm({ name: role.name, codenames: new Set(role.permissions.map((p) => p.codename_full)) });
    setError("");
  };

  const togglePermission = (codename: string) => {
    setForm((f) => {
      const next = new Set(f.codenames);
      if (next.has(codename)) next.delete(codename);
      else next.add(codename);
      return { ...f, codenames: next };
    });
  };

  const handleSave = async () => {
    if (!form.name.trim()) { setError("Name is required."); return; }
    setSaving(true);
    setError("");
    try {
      const payload = { name: form.name.trim(), permission_codenames: Array.from(form.codenames) };
      if (editing) {
        await rolesApi.update(editing.id, payload);
      } else {
        await rolesApi.create(payload);
      }
      setEditing(null);
      setForm({ name: "", codenames: new Set() });
      load();
    } catch (e: unknown) {
      setError(extractApiError(e, "Could not save role."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (role: Role) => {
    if (!confirm(`Delete role "${role.name}"? Anyone currently holding it will lose its permissions.`)) return;
    await rolesApi.delete(role.id);
    setRoles((r) => r.filter((x) => x.id !== role.id));
  };

  const isFormOpen = editing !== null || form.name !== "" || form.codenames.size > 0;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Roles</h1>
          <p className="text-sm text-gray-500 mt-0.5">{roles.length} role{roles.length === 1 ? "" : "s"}</p>
        </div>
        {canManageRoles && !isFormOpen && (
          <Button onClick={openCreate}>
            <Plus size={15} className="mr-1.5" />
            New role
          </Button>
        )}
      </div>

      {isFormOpen && canManageRoles ? (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">{editing ? `Edit "${editing.name}"` : "New role"}</h2>
            <button onClick={() => { setEditing(null); setForm({ name: "", codenames: new Set() }); }}
              className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
              <X size={16} />
            </button>
          </div>
          <Input id="role_name" label="Role name *" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />

          <div>
            <label className="text-xs font-medium text-gray-600 mb-2 block">Permissions</label>
            <div className="space-y-4 max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-4">
              {Object.entries(groupedPermissions).map(([appLabel, perms]) => (
                <div key={appLabel}>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-1.5">{appLabel}</p>
                  <div className="space-y-1">
                    {perms.map((p) => (
                      <label key={p.id} className="flex items-start gap-2 cursor-pointer py-0.5">
                        <input
                          type="checkbox"
                          checked={form.codenames.has(p.codename_full)}
                          onChange={() => togglePermission(p.codename_full)}
                          className="mt-0.5 rounded"
                        />
                        <span className="text-sm text-gray-700">{p.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              {!Object.keys(groupedPermissions).length && (
                <p className="text-xs text-gray-400">No permissions available to assign.</p>
              )}
            </div>
            <p className="text-[11px] text-gray-400 mt-1.5">
              Only your own permissions are selectable — you can&apos;t define a role more powerful than yourself.
            </p>
          </div>

          {error && <p className="text-xs text-danger-600">{error}</p>}

          <div className="flex gap-2">
            <Button variant="outline" size="sm"
              onClick={() => { setEditing(null); setForm({ name: "", codenames: new Set() }); }} className="flex-1">
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} isLoading={saving} className="flex-1">
              {editing ? "Save changes" : "Create role"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-sm text-gray-400">Loading roles…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    {["Role", "Permissions", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {roles.map((role) => (
                    <tr key={role.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <RoleBadge name={role.name} />
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {role.permission_count} permission{role.permission_count === 1 ? "" : "s"}
                      </td>
                      <td className="px-4 py-3">
                        {canManageRoles && (
                          <div className="flex items-center gap-2 justify-end">
                            <button onClick={() => openEdit(role)} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100">
                              <Pencil size={14} />
                            </button>
                            <button onClick={() => handleDelete(role)} className="p-1.5 rounded-lg text-gray-400 hover:text-danger-600 hover:bg-danger-50">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!roles.length && (
                    <tr><td colSpan={3} className="px-4 py-10 text-center text-sm text-gray-400">No roles yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
