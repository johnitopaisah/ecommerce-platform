"use client";

import { useRouter, usePathname } from "next/navigation";
import type { Category } from "@/types";
import { cn } from "@/lib/utils";

interface Props {
  categories: Category[];
  currentParams: Record<string, string | undefined>;
}

export default function ProductFilters({ categories, currentParams }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const updateParam = (key: string, value: string | undefined) => {
    const params = new URLSearchParams(
      Object.entries(currentParams).reduce((acc, [k, v]) => {
        if (v) acc[k] = v;
        return acc;
      }, {} as Record<string, string>)
    );
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    // Reset to page 1 on filter change
    params.delete("page");
    router.push(`${pathname}?${params.toString()}`);
  };

  const clearAll = () => router.push(pathname);

  return (
    <div className="space-y-6">
      {/* Clear filters */}
      {Object.values(currentParams).some(Boolean) && (
        <button
          onClick={clearAll}
          className="text-sm text-red-600 hover:underline"
        >
          Clear all filters
        </button>
      )}

      {/* Category */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Category</h3>
        <ul className="space-y-1.5">
          <li>
            <button
              onClick={() => updateParam("category", undefined)}
              className={cn(
                "text-sm w-full text-left px-2 py-1 rounded hover:bg-gray-100",
                !currentParams.category
                  ? "font-semibold text-gray-900"
                  : "text-gray-600"
              )}
            >
              All
            </button>
          </li>
          {categories.map((cat) => (
            <li key={cat.id}>
              <button
                onClick={() => updateParam("category", cat.slug)}
                className={cn(
                  "text-sm w-full text-left px-2 py-1 rounded hover:bg-gray-100",
                  currentParams.category === cat.slug
                    ? "font-semibold text-gray-900"
                    : "text-gray-600"
                )}
              >
                {cat.name}
                <span className="ml-1 text-xs text-gray-400">
                  ({cat.product_count})
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Price range */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Price</h3>
        <div className="flex items-center gap-2">
          <input
            type="number"
            placeholder="Min"
            defaultValue={currentParams.min_price}
            onBlur={(e) => updateParam("min_price", e.target.value || undefined)}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
          />
          <span className="text-gray-400">–</span>
          <input
            type="number"
            placeholder="Max"
            defaultValue={currentParams.max_price}
            onBlur={(e) => updateParam("max_price", e.target.value || undefined)}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>
      </div>

      {/* In stock */}
      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={currentParams.in_stock === "true"}
            onChange={(e) =>
              updateParam("in_stock", e.target.checked ? "true" : undefined)
            }
            className="rounded border-gray-300"
          />
          <span className="text-sm text-gray-700">In stock only</span>
        </label>
      </div>

      {/* Ordering */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Sort by</h3>
        <select
          value={currentParams.ordering || "-created"}
          onChange={(e) => updateParam("ordering", e.target.value)}
          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
        >
          <option value="-created">Newest first</option>
          <option value="created">Oldest first</option>
          <option value="price">Price: low to high</option>
          <option value="-price">Price: high to low</option>
          <option value="title">Name: A–Z</option>
          <option value="-title">Name: Z–A</option>
        </select>
      </div>
    </div>
  );
}
