import { notFound } from "next/navigation";
import { productsApi } from "@/lib/services";
import ProductDetailClient from "./ProductDetailClient";
import type { Product } from "@/types";

export const dynamic = "force-dynamic";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let product: Product | null = null;

  try {
    const res = await productsApi.detail(slug);
    product = res.data;
  } catch {
    notFound();
  }

  if (!product) notFound();

  return <ProductDetailClient product={product} />;
}
