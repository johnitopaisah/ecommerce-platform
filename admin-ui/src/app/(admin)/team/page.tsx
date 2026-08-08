"use client";

import { useEffect, useState } from "react";
import { UserPlus, CheckCircle, XCircle, X } from "lucide-react";
import { teamApi, rolesApi } from "@/lib/services";
import { usePermissionsStore } from "@/store/permissionsStore";
import type { TeamMember, Role } from "@/types";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import RoleBadge, { SuperAdminBadge } from "@/components/rbac/RoleBadge";
import DurationSelect from "@/components/rbac/DurationSelect";

interface FormState {
  email: string;
  user_name: string;
  first_name: string;
  last_name: string;
  initial_group_id: string;
  duration_hours: number | null;
}

const emptyForm: FormState = {
  email: "", user_name: "", first_name: "", last_name: "",
  initial_group_id: "", duration_hours: null,
};

export default function TeamMembersPage() {
  const { hasPermission, permissions, isSuperuser } = usePermissionsStore();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const canCreate = hasPermission("account.manage_staff");

  const load = () => {
    setLoading(true);
    Promise.all([teamApi.list(), rolesApi.list()])
      .then(([membersRes, rolesRes]) => {
        setMembers(membersRes.data);
        setRoles(rolesRes.data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // Only offer roles the current user could actually grant — mirrors the
  // backend's subset-rule check so the form doesn't invite a 403. Not a
  // security boundary (the API enforces that), just avoids a dead end.
  const grantableRoles = isSuperuser
    ? roles
    : roles.filter((r) => r.permissions.every((p) => permissions.includes(p.codename_full)));

  const handleCreate = async () => {
    if (!form.email.trim() || !form.user_name.trim()) {
      setError("Email and username are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await teamApi.create({
        email: form.email.trim(),
        user_name: form.user_name.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        initial_group_id: form.initial_group_id ? Number(form.initial_group_id) : undefined,
        duration_hours: form.duration_hours ?? undefined,
      });
      setShowForm(false);
      setForm(emptyForm);
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string, string[] | string> } };
      const data = err?.response?.data;
      const firstError = data ? Object.values(data)[0] : null;
      setError((Array.isArray(firstError) ? firstError[0] : firstError) || "Could not create team member.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {members.length} team member{members.length === 1 ? "" : "s"} — internal staff, distinct from customer accounts
          </p>
        </div>
        {canCreate && (
          <Button onClick={() => setShowForm(true)}>
            <UserPlus size={15} className="mr-1.5" />
            Add team member
          </Button>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading team…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {["Member", "Roles", "Active", "Joined", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {members.map((member) => (
                  <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{member.full_name || member.user_name}</p>
                      <p className="text-xs text-gray-400">{member.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1.5 max-w-md">
                        {member.is_superuser && <SuperAdminBadge />}
                        {member.roles.map((r) => (
                          <RoleBadge key={r.grant_id} name={r.group_name} expiresAt={r.expires_at} />
                        ))}
                        {!member.is_superuser && !member.roles.length && (
                          <span className="text-xs text-gray-400">No roles assigned</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {member.is_active
                        ? <CheckCircle size={15} className="text-success-600" />
                        : <XCircle size={15} className="text-gray-300" />}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(member.created)}</td>
                    <td className="px-4 py-3" />
                  </tr>
                ))}
                {!members.length && (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-sm text-gray-400">No team members yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-center justify-center p-4" onClick={() => setShowForm(false)}>
          <div
            className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="font-bold text-gray-900">Add team member</h2>
              <button onClick={() => setShowForm(false)} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-xs text-gray-500 -mt-1">
                They&apos;ll receive an email to set their own password — nobody here ever sets it for them.
              </p>
              <Input id="email" label="Email *" type="email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
              <Input id="user_name" label="Username *" value={form.user_name}
                onChange={(e) => setForm({ ...form, user_name: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <Input id="first_name" label="First name" value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                <Input id="last_name" label="Last name" value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Initial role (optional)</label>
                <select
                  value={form.initial_group_id}
                  onChange={(e) => setForm({ ...form, initial_group_id: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  <option value="">No role — grant one later</option>
                  {grantableRoles.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
                {roles.length > grantableRoles.length && (
                  <p className="text-[11px] text-gray-400">
                    Only showing roles within your own permissions — {roles.length - grantableRoles.length} other role(s) hidden.
                  </p>
                )}
              </div>

              {form.initial_group_id && (
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-gray-600">Duration</label>
                  <DurationSelect
                    value={form.duration_hours}
                    onChange={(hours) => setForm({ ...form, duration_hours: hours })}
                  />
                </div>
              )}

              {error && <p className="text-xs text-danger-600">{error}</p>}

              <div className="flex gap-2 pt-2">
                <Button variant="outline" size="sm" onClick={() => setShowForm(false)} className="flex-1">
                  Cancel
                </Button>
                <Button size="sm" onClick={handleCreate} isLoading={saving} className="flex-1">
                  Create account
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
