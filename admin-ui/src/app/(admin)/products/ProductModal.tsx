"use client";

import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, Upload, ImageIcon } from "lucide-react";
import { productsApi } from "@/lib/services";
import type { ProductWritePayload } from "@/lib/services";
import type { Product, Category } from "@/types";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import Image from "next/image";

const schema = z.object({
  title: z.string().min(2, "Title is required"),
  description: z.string().optional(),
  category_id: z.number().int().min(1, "Category is required"),
  price: z.number().positive("Price must be positive"),
  discount_price: z.number().positive().optional(),
  stock_quantity: z.number().int().min(0, "Stock must be 0 or more"),
  is_active: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  product: Product | null;
  categories: Category[];
  onSave: () => void;
  onClose: () => void;
}

export default function ProductModal({ product, categories, onSave, onClose }: Props) {
  const isEdit = !!product;
  const fileInputRef = useRef<HTMLInputElement>(null);

  // imageFile holds a newly selected file (null = no new file chosen yet)
  const [imageFile, setImageFile] = useState<File | null>(null);
  // imageFileUrl is the blob URL for the newly selected file
  const [imageFileUrl, setImageFileUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState("");

  // Derived: show the new file preview if one was chosen, otherwise show the
  // existing product image. No setState in effects needed.
  const imagePreview = imageFileUrl ?? (product?.image || null);

  const { register, handleSubmit, reset, setValue, formState: { errors, isSubmitting } } =
    useForm<FormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        title: product?.title || "",
        description: product?.description || "",
        category_id: product?.category?.id || 0,
        price: product ? parseFloat(product.price) : 0,
        discount_price: product?.discount_price ? parseFloat(product.discount_price) : undefined,
        stock_quantity: product?.stock_quantity || 0,
        is_active: product?.is_active ?? true,
      },
    });

  // Only reset the form fields — no setState for image here
  useEffect(() => {
    if (product) {
      reset({
        title: product.title,
        description: product.description,
        category_id: product.category?.id || 0,
        price: parseFloat(product.price),
        discount_price: product.discount_price ? parseFloat(product.discount_price) : undefined,
        stock_quantity: product.stock_quantity,
        is_active: product.is_active,
      });
    }
  }, [product, reset]);

  // Revoke blob URL on unmount to avoid memory leaks
  useEffect(() => {
    return () => {
      if (imageFileUrl) URL.revokeObjectURL(imageFileUrl);
    };
  }, [imageFileUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setImageError("Please select an image file (JPG, PNG, WebP).");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setImageError("Image must be smaller than 5MB.");
      return;
    }
    if (imageFileUrl) URL.revokeObjectURL(imageFileUrl);
    setImageError("");
    setImageFile(file);
    setImageFileUrl(URL.createObjectURL(file));
  };

  const handleRemoveImage = () => {
    if (imageFileUrl) URL.revokeObjectURL(imageFileUrl);
    setImageFile(null);
    setImageFileUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onSubmit = async (data: FormData) => {
    setImageError("");

    const payload: ProductWritePayload = {
      title: data.title,
      description: data.description,
      category_id: data.category_id,
      price: data.price,
      discount_price: data.discount_price,
      stock_quantity: data.stock_quantity,
      is_active: data.is_active,
    };

    let savedSlug = product?.slug;

    try {
      if (isEdit && product) {
        await productsApi.update(product.slug, payload);
      } else {
        const res = await productsApi.create(payload);
        savedSlug = res.data.slug;
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: unknown } };
      const detail = JSON.stringify(e?.response?.data ?? "Unknown error");
      setImageError(`Save failed: ${detail}`);
      return;
    }

    if (imageFile && savedSlug) {
      try {
        await productsApi.uploadImage(savedSlug, imageFile);
      } catch {
        setImageError("Product saved but image upload failed. You can add it later.");
        onSave();
        return;
      }
    }

    onSave();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">
            {isEdit ? "Edit product" : "Add product"}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-4">

          {/* Image upload */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Product image</label>

            {imagePreview ? (
              <div className="relative w-full h-48 rounded-xl overflow-hidden border border-gray-200 bg-gray-50 group">
                <Image
                  src={imagePreview}
                  alt="Product preview"
                  fill
                  className="object-contain"
                  unoptimized
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-white text-gray-900 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-gray-100"
                  >
                    Change
                  </button>
                  <button
                    type="button"
                    onClick={handleRemoveImage}
                    className="bg-red-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-red-600"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full h-36 border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center gap-2 text-gray-400 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                <Upload size={24} />
                <span className="text-sm font-medium">Click to upload image</span>
                <span className="text-xs">JPG, PNG, WebP — max 5MB</span>
              </button>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />

            {imageError && (
              <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 break-all">
                {imageError}
              </p>
            )}

            {!imagePreview && !isEdit && (
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <ImageIcon size={11} /> You can also add images after creating the product
              </p>
            )}
          </div>

          {/* Fields */}
          <Input id="title" label="Title *" {...register("title")} error={errors.title?.message} />

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Category *</label>
            <select
              defaultValue={product?.category?.id || 0}
              onChange={(e) => setValue("category_id", parseInt(e.target.value, 10))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
            >
              <option value={0}>Select a category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            {errors.category_id && (
              <p className="text-xs text-red-500">{errors.category_id.message}</p>
            )}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-600">Description</label>
            <textarea
              {...register("description")}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              id="price" label="Price (£) *" type="number" step="0.01"
              {...register("price", { valueAsNumber: true })}
              error={errors.price?.message}
            />
            <Input
              id="discount_price" label="Sale price (£)" type="number" step="0.01"
              placeholder="Optional"
              {...register("discount_price", { valueAsNumber: true })}
            />
          </div>

          <Input
            id="stock_quantity" label="Stock quantity *" type="number"
            {...register("stock_quantity", { valueAsNumber: true })}
            error={errors.stock_quantity?.message}
          />

          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" {...register("is_active")} className="rounded border-gray-300" />
            <span className="text-sm text-gray-700">Active (visible to customers)</span>
          </label>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" className="flex-1" isLoading={isSubmitting}>
              {isEdit ? "Save changes" : "Create product"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
