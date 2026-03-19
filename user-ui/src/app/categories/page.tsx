import Link from "next/link";
import { categoriesApi } from "@/lib/services";
import type { Metadata } from "next";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Categories" };

export default async function CategoriesPage() {
  let categories: Awaited<ReturnType<typeof categoriesApi.list>>["data"] = [];

  try {
    const res = await categoriesApi.list();
    categories = res.data;
  } catch {
    // API unavailable — render empty state
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">All Categories</h1>
      {categories.length === 0 ? (
        <p className="text-gray-500">No categories available.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              href={`/categories/${cat.slug}`}
              className="group bg-white border border-gray-200 rounded-xl p-6 hover:border-gray-900 hover:shadow-sm transition-all"
            >
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-gray-700 mb-1">
                {cat.name}
              </h2>
              <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                {cat.description}
              </p>
              <span className="text-xs text-gray-400">
                {cat.product_count} {cat.product_count === 1 ? "product" : "products"}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
