import { categoriesApi } from "@/lib/services";
import ProductGrid from "@/components/products/ProductGrid";
import Pagination from "@/components/products/Pagination";
import SortSelect from "@/components/products/SortSelect";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import type { Product } from "@/types";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 20;

interface Props {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ ordering?: string; page?: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const res = await categoriesApi.detail(slug);
    return { title: res.data.name };
  } catch {
    return { title: "Category" };
  }
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const query = await searchParams;

  let categoryName = "";
  let categoryDescription = "";
  let categoryProductCount = 0;
  let products: Product[] = [];
  let count = 0;

  try {
    const [catRes, productsRes] = await Promise.all([
      categoriesApi.detail(slug),
      categoriesApi.products(slug, {
        ordering: query.ordering || "-created",
        page: query.page ? Number(query.page) : 1,
      }),
    ]);
    categoryName = catRes.data.name;
    categoryDescription = catRes.data.description;
    categoryProductCount = catRes.data.product_count;
    products = productsRes.data.results ?? [];
    count = productsRes.data.count;
  } catch {
    notFound();
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-start justify-between gap-4 flex-wrap mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{categoryName}</h1>
          {categoryDescription && (
            <p className="text-gray-500 mt-1">{categoryDescription}</p>
          )}
          <p className="text-sm text-gray-400 mt-1">{categoryProductCount} products</p>
        </div>
        {count > 0 && (
          <SortSelect currentOrdering={query.ordering} otherParams={query} />
        )}
      </div>
      <ProductGrid products={products} emptyMessage="No products in this category yet." />
      <Pagination
        currentPage={query.page ? Number(query.page) : 1}
        totalCount={count}
        pageSize={PAGE_SIZE}
        basePath={`/categories/${slug}`}
        searchParams={query}
      />
    </div>
  );
}
