import Link from "next/link";
import { categoriesApi, productsApi } from "@/lib/services";
import ProductGrid from "@/components/products/ProductGrid";
import { Button } from "@/components/ui/Button";
import type { Category, Product } from "@/types";

async function getHomeData() {
  try {
    const [categoriesRes, productsRes] = await Promise.all([
      categoriesApi.list(),
      productsApi.list({ page_size: 8, ordering: "-created" }),
    ]);
    return {
      categories: categoriesRes.data as Category[],
      products: productsRes.data.results as Product[],
    };
  } catch {
    return { categories: [], products: [] };
  }
}

export default async function HomePage() {
  const { categories, products } = await getHomeData();

  return (
    <div>
      {/* Hero */}
      <section className="bg-gray-900 text-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight">
            Shop the best products,<br className="hidden md:block" /> at the best prices.
          </h1>
          <p className="text-gray-300 text-lg mb-8 max-w-xl mx-auto">
            Thousands of products across electronics, clothing, home and more.
            Free delivery on orders over £50.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/products">
              <Button size="lg" variant="secondary">
                Shop now
              </Button>
            </Link>
            <Link href="/categories">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                Browse categories
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Shop by category</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              href={`/categories/${cat.slug}`}
              className="group bg-white border border-gray-200 rounded-xl p-4 text-center hover:border-gray-900 hover:shadow-sm transition-all"
            >
              <p className="font-semibold text-gray-900 text-sm group-hover:text-gray-700">
                {cat.name}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {cat.product_count} {cat.product_count === 1 ? "item" : "items"}
              </p>
            </Link>
          ))}
        </div>
      </section>

      {/* New arrivals */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">New arrivals</h2>
          <Link
            href="/products"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 underline underline-offset-2"
          >
            View all →
          </Link>
        </div>
        <ProductGrid products={products} />
      </section>
    </div>
  );
}
