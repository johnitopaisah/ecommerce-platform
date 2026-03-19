import { notFound } from "next/navigation";
import { productsApi } from "@/lib/services";
import ProductDetailClient from "./ProductDetailClient";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  try {
    const res = await productsApi.detail(slug);
    return <ProductDetailClient product={res.data} />;
  } catch {
    notFound();
  }
}
