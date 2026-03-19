import { productsApi, categoriesApi } from "@/lib/services";
import ProductGrid from "@/components/products/ProductGrid";
import ProductFilters from "@/components/products/ProductFilters";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "All Products" };

interface Props {
  searchParams: Promise<{
    category?: string;
    search?: string;
    min_price?: string;
    max_price?: string;
    in_stock?: string;
    ordering?: string;
    page?: string;
  }>;
}

export default async function ProductsPage({ searchParams }: Props) {
  const params = await searchParams;

  const [productsRes, categoriesRes] = await Promise.all([
    productsApi.list({
      category: params.category,
      search: params.search,
      min_price: params.min_price ? Number(params.min_price) : undefined,
      max_price: params.max_price ? Number(params.max_price) : undefined,
      in_stock: params.in_stock === "true" ? true : undefined,
      ordering: params.ordering || "-created",
      page: params.page ? Number(params.page) : 1,
    }),
    categoriesApi.list(),
  ]);

  const { results: products, count } = productsRes.data;
  const categories = categoriesRes.data;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {params.search ? `Results for "${params.search}"` : "All Products"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">{count} products</p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Filters sidebar */}
        <aside className="md:w-56 shrink-0">
          <ProductFilters categories={categories} currentParams={params} />
        </aside>

        {/* Grid */}
        <div className="flex-1">
          <ProductGrid
            products={products}
            emptyMessage="No products match your filters."
          />
        </div>
      </div>
    </div>
  );
}
