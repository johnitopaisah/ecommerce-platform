"use client";

import { useEffect, useState } from "react";
import { Plus, Check, X, Ban } from "lucide-react";
import { rbacApi, rolesApi } from "@/lib/services";
import type { RoleGrantRequest, Role, RequestStatus } from "@/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import DurationSelect from "@/components/rbac/DurationSelect";
import { useToastStore } from "@/store/toastStore";

const STATUS_STYLES: Record<RequestStatus, string> = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  approved: "bg-success-50 text-success-700 border-green-200",
  denied: "bg-danger-50 text-danger-700 border-red-200",
  cancelled: "bg-gray-50 text-gray-500 border-gray-200",
};

export default function AccessRequestsPage() {
  const { show } = useToastStore();
  const [tab, setTab] = useState<"mine" | "pending">("pending");
  const [myRequests, setMyRequests] = useState<RoleGrantRequest[]>([]);
  const [pending, setPending] = useState<RoleGrantRequest[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [groupId, setGroupId] = useState("");
  const [durationHours, setDurationHours] = useState<number | null>(null);
  const [justification, setJustification] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = () => {
    setLoading(true);
    Promise.all([rbacApi.myRequests(), rbacApi.pendingRequests(), rolesApi.list()])
      .then(([mineRes, pendingRes, rolesRes]) => {
        setMyRequests(mineRes.data);
        setPending(pendingRes.data);
        setRoles(rolesRes.data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSubmitRequest = async () => {
    if (!groupId || !justification.trim()) {
      setFormError("A role and a justification are both required.");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await rbacApi.requestRole({
        group_id: Number(groupId), duration_hours: durationHours, justification: justification.trim(),
      });
      setShowForm(false);
      setGroupId(""); setDurationHours(null); setJustification("");
      show("Request submitted.", "success");
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: Record<string, string[] | string> } };
      const data = err?.response?.data;
      const firstError = data ? Object.values(data)[0] : null;
      setFormError((Array.isArray(firstError) ? firstError[0] : firstError) || "Could not submit request.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (req: RoleGrantRequest) => {
    if (!confirm("Cancel this request?")) return;
    await rbacApi.cancelRequest(req.id);
    show("Request cancelled.", "info");
    load();
  };

  const handleApprove = async (req: RoleGrantRequest) => {
    try {
      await rbacApi.approveRequest(req.id);
      show(`Approved — ${req.requester_email} now holds ${req.group_name}.`, "success");
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      show(err?.response?.data?.detail || "Could not approve.", "error");
    }
  };

  const handleDeny = async (req: RoleGrantRequest) => {
    const reason = prompt("Reason for denial (optional):") || "";
    await rbacApi.denyRequest(req.id, reason);
    show("Request denied.", "info");
    load();
  };

  const activeList = tab === "mine" ? myRequests : pending;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Access Requests</h1>
          <p className="text-sm text-gray-500 mt-0.5">Request a role, or review requests you&apos;re qualified to approve</p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus size={15} className="mr-1.5" />
          Request a role
        </Button>
      </div>

      <div className="flex bg-gray-100 rounded-lg p-1 gap-1 w-fit">
        <button
          onClick={() => setTab("pending")}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            tab === "pending" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Pending my approval {pending.length > 0 && `(${pending.length})`}
        </button>
        <button
          onClick={() => setTab("mine")}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            tab === "mine" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
          }`}
        >
          My requests
        </button>
      </div>

      <div className="space-y-3">
        {loading ? (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-sm text-gray-400">Loading…</div>
        ) : !activeList.length ? (
          <div className="bg-white border border-gray-200 rounded-xl p-10 text-center text-sm text-gray-400">
            {tab === "pending" ? "No requests waiting on your approval." : "You haven't requested any roles yet."}
          </div>
        ) : (
          activeList.map((req) => (
            <div key={req.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-gray-900">{req.group_name}</p>
                    <Badge className={STATUS_STYLES[req.status]}>{req.status}</Badge>
                    {req.duration_hours && <span className="text-xs text-gray-400">for {req.duration_hours}h</span>}
                    {!req.duration_hours && <span className="text-xs text-gray-400">permanent</span>}
                  </div>
                  {tab === "pending" && (
                    <p className="text-sm text-gray-600 mt-1">Requested by {req.requester_email}</p>
                  )}
                  <p className="text-sm text-gray-500 mt-1.5">&ldquo;{req.justification}&rdquo;</p>
                  <p className="text-xs text-gray-400 mt-1.5">{formatDate(req.created)}</p>
                  {req.decision_reason && (
                    <p className="text-xs text-gray-500 mt-1.5">Decision note: {req.decision_reason}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {tab === "pending" && req.status === "pending" && (
                    <>
                      <Button size="sm" variant="primary" onClick={() => handleApprove(req)}>
                        <Check size={14} className="mr-1" /> Approve
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => handleDeny(req)}>
                        <X size={14} className="mr-1" /> Deny
                      </Button>
                    </>
                  )}
                  {tab === "mine" && req.status === "pending" && (
                    <button
                      onClick={() => handleCancel(req)}
                      title="Cancel request"
                      className="p-1.5 rounded-lg text-gray-400 hover:text-danger-600 hover:bg-danger-50"
                    >
                      <Ban size={15} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-center justify-center p-4" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="font-bold text-gray-900">Request a role</h2>
              <button onClick={() => setShowForm(false)} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Role *</label>
                <select
                  value={groupId}
                  onChange={(e) => setGroupId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
                >
                  <option value="">Select a role…</option>
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Duration</label>
                <DurationSelect value={durationHours} onChange={setDurationHours} />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Justification *</label>
                <textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  rows={3}
                  placeholder="Why do you need this?"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gray-900"
                />
              </div>
              {formError && <p className="text-xs text-danger-600">{formError}</p>}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setShowForm(false)} className="flex-1">
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSubmitRequest} isLoading={submitting} className="flex-1">
                  Submit request
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
