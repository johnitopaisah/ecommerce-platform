"use client";

import { useRouter, usePathname } from "next/navigation";

interface Props {
  currentOrdering?: string;
  otherParams: Record<string, string | undefined>;
}

export default function SortSelect({ currentOrdering, otherParams }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const handleChange = (ordering: string) => {
    const params = new URLSearchParams(
      Object.entries(otherParams).reduce((acc, [k, v]) => {
        if (v && k !== "ordering" && k !== "page") acc[k] = v;
        return acc;
      }, {} as Record<string, string>)
    );
    if (ordering !== "-created") params.set("ordering", ordering);
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  };

  return (
    <select
      value={currentOrdering || "-created"}
      onChange={(e) => handleChange(e.target.value)}
      className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-gray-700"
    >
      <option value="-created">Newest first</option>
      <option value="created">Oldest first</option>
      <option value="price">Price: low to high</option>
      <option value="-price">Price: high to low</option>
      <option value="title">Name: A–Z</option>
      <option value="-title">Name: Z–A</option>
    </select>
  );
}
