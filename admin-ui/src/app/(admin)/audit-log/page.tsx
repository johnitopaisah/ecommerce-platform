"use client";

import { Fragment, useEffect, useState } from "react";
import { Search, ChevronDown, ChevronUp } from "lucide-react";
import { auditLogApi } from "@/lib/services";
import type { AuditLogEntry } from "@/types";
import { Badge } from "@/components/ui/Badge";

const OUTCOME_STYLES: Record<string, string> = {
  success: "bg-success-50 text-success-700 border-green-200",
  denied: "bg-danger-50 text-danger-700 border-red-200",
  error: "bg-amber-50 text-amber-700 border-amber-200",
};

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [outcome, setOutcome] = useState<string>("");
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  // Never calls setState synchronously — only inside .then/.finally, so
  // this is safe to call from the mount effect below without triggering a
  // render-effect-setState cascade. Callers that need the loading skeleton
  // to reappear (filter/search changes, not the initial mount — `loading`
  // already starts true) set it themselves right before calling load().
  const load = (currentOutcome: string, currentSearch: string) => {
    auditLogApi.list({
      outcome: currentOutcome || undefined,
      search: currentSearch || undefined,
    })
      .then((res) => setEntries(res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load("", "");
  }, []);

  const handleOutcomeChange = (value: string) => {
    setOutcome(value);
    setLoading(true);
    load(value, search);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    load(outcome, search);
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
        <p className="text-sm text-gray-500 mt-0.5">Who did what — read-only, append-only, most recent 500 entries</p>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
          {[
            { label: "All", value: "" },
            { label: "Success", value: "success" },
            { label: "Denied", value: "denied" },
            { label: "Error", value: "error" },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => handleOutcomeChange(f.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                outcome === f.value ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <form onSubmit={handleSearch} className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search target…"
            className="pl-8 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 w-64"
          />
        </form>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {["When", "Actor", "Action", "Target", "Outcome", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {entries.map((entry) => (
                  <Fragment key={entry.id}>
                    <tr
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                    >
                      <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                        {new Date(entry.created).toLocaleString("en-GB")}
                      </td>
                      <td className="px-4 py-3 text-gray-700">{entry.actor_email || "system"}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-900">{entry.action}</td>
                      <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{entry.target}</td>
                      <td className="px-4 py-3">
                        <Badge className={OUTCOME_STYLES[entry.outcome] || ""}>{entry.outcome}</Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-400">
                        {expanded === entry.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </td>
                    </tr>
                    {expanded === entry.id && (
                      <tr>
                        <td colSpan={6} className="px-4 py-3 bg-gray-50">
                          <div className="text-xs text-gray-600 space-y-1">
                            {entry.ip_address && <p><span className="font-medium">IP:</span> {entry.ip_address}</p>}
                            <pre className="bg-white border border-gray-200 rounded-lg p-3 overflow-x-auto font-mono text-[11px]">
                              {JSON.stringify(entry.detail, null, 2)}
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                {!entries.length && (
                  <tr><td colSpan={6} className="px-4 py-10 text-center text-sm text-gray-400">No entries found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
