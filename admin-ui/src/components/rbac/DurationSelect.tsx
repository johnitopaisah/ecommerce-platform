"use client";

import { useState } from "react";

const PRESETS = [
  { label: "Permanent", hours: null },
  { label: "4 hours", hours: 4 },
  { label: "1 day", hours: 24 },
  { label: "1 week", hours: 168 },
  { label: "Custom", hours: "custom" as const },
];

interface DurationSelectProps {
  value: number | null;
  onChange: (hours: number | null) => void;
}

export default function DurationSelect({ value, onChange }: DurationSelectProps) {
  const [customMode, setCustomMode] = useState(false);

  const handlePreset = (hours: number | null | "custom") => {
    if (hours === "custom") {
      setCustomMode(true);
      return;
    }
    setCustomMode(false);
    onChange(hours);
  };

  const activePreset = customMode
    ? "Custom"
    : PRESETS.find((p) => p.hours === value)?.label ?? "Custom";

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => handlePreset(p.hours)}
            className={`px-2.5 py-1 text-xs font-medium rounded-full border transition-colors ${
              activePreset === p.label
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      {customMode && (
        <input
          type="number"
          min={1}
          placeholder="Hours"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
          className="w-32 border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
        />
      )}
    </div>
  );
}
