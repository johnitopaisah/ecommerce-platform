import { categoriesApi } from "@/lib/services";
import ProductGrid from "@/components/products/ProductGrid";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ slug: string }>;
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

export default async function CategoryPage({ params }: Props) {
  const { slug } = await params;

  try {
    const [catRes, productsRes] = await Promise.all([
      categoriesApi.detail(slug),
      categoriesApi.products(slug),
    ]);

    const category = catRes.data;
    const products = productsRes.data.results;

    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">{category.name}</h1>
          {category.description && (
            <p className="text-gray-500 mt-1">{category.description}</p>
          )}
          <p className="text-sm text-gray-400 mt-1">
            {category.product_count} products
          </p>
        </div>
        <ProductGrid products={products} emptyMessage="No products in this category yet." />
      </div>
    );
  } catch {
    notFound();
  }
}
