import { Clock, Crown } from "lucide-react";
import { formatTimeUntil } from "@/lib/utils";

// Deterministic color per role name (hash-based) — no backend "category"
// field needed to still get visually distinct, consistent badges across
// the whole app. Super Admin gets its own fixed treatment below since
// it's not a real Group (it's the unconditional is_superuser bypass).
const PALETTE = [
  "bg-blue-50 text-blue-700 border-blue-200",
  "bg-purple-50 text-purple-700 border-purple-200",
  "bg-emerald-50 text-emerald-700 border-emerald-200",
  "bg-amber-50 text-amber-700 border-amber-200",
  "bg-rose-50 text-rose-700 border-rose-200",
  "bg-cyan-50 text-cyan-700 border-cyan-200",
  "bg-indigo-50 text-indigo-700 border-indigo-200",
  "bg-teal-50 text-teal-700 border-teal-200",
];

function colorForRole(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

interface RoleBadgeProps {
  name: string;
  expiresAt?: string | null;
}

export default function RoleBadge({ name, expiresAt }: RoleBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${colorForRole(name)}`}
    >
      {name}
      {expiresAt && (
        <span className="inline-flex items-center gap-0.5 opacity-75">
          <Clock size={10} />
          {formatTimeUntil(expiresAt)}
        </span>
      )}
    </span>
  );
}

export function SuperAdminBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border bg-gray-900 text-white border-gray-900">
      <Crown size={10} />
      Super Admin
    </span>
  );
}
