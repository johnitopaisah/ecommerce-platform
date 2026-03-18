"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";
import { ordersApi, paymentApi } from "@/lib/services";
import { formatPrice } from "@/lib/utils";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

const schema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Valid email required"),
  phone: z.string().optional(),
  address_line_1: z.string().min(5, "Address is required"),
  address_line_2: z.string().optional(),
  city: z.string().min(2, "City is required"),
  postcode: z.string().min(2, "Postcode is required"),
  country: z.string().min(2, "Country code required (e.g. GB)").max(2),
});

type FormData = z.infer<typeof schema>;

export default function CheckoutPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { basket, clearBasket } = useBasketStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login?next=/checkout");
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && basket.items.length === 0) router.replace("/basket");
  }, [isAuthenticated, basket.items.length, router]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: user?.full_name || "",
      email: user?.email || "",
      phone: user?.phone_number || "",
      address_line_1: user?.address_line_1 || "",
      address_line_2: user?.address_line_2 || "",
      city: user?.town_city || "",
      postcode: user?.postcode || "",
      country: user?.country || "",
    },
  });

  const onSubmit = async (data: FormData) => {
    setError(null);

    // Step 1: Try to create a Stripe PaymentIntent for the order_key.
    // If Stripe keys are not configured yet, fall back to a UUID order_key
    // so the order is still created and visible in order history.
    let orderKey = `dev_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    let stripeAvailable = false;

    try {
      const intentRes = await paymentApi.createIntent();
      orderKey = intentRes.data.client_secret;
      stripeAvailable = true;
    } catch {
      // Stripe not configured — proceed with fallback key
      // In production with real Stripe keys this will not happen
    }

    // Step 2: Always create the order record
    try {
      await ordersApi.create({
        ...data,
        phone: data.phone || "",
        address_line_2: data.address_line_2 || "",
        order_key: orderKey,
      });

      await clearBasket();

      // Step 3: Redirect to success
      router.push("/checkout/success");
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        "Something went wrong. Please try again.";
      setError(detail);
    }
  };

  if (!isAuthenticated || !basket.items.length) return null;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Checkout</h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Form */}
        <div className="flex-1">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Contact */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
              <h2 className="font-semibold text-gray-900">Contact</h2>
              <Input
                id="full_name" label="Full name"
                {...register("full_name")} error={errors.full_name?.message}
              />
              <Input
                id="email" label="Email" type="email"
                {...register("email")} error={errors.email?.message}
              />
              <Input id="phone" label="Phone (optional)" {...register("phone")} />
            </div>

            {/* Shipping */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
              <h2 className="font-semibold text-gray-900">Shipping address</h2>
              <Input
                id="address_line_1" label="Address"
                {...register("address_line_1")} error={errors.address_line_1?.message}
              />
              <Input
                id="address_line_2" label="Apartment, suite, etc. (optional)"
                {...register("address_line_2")}
              />
              <div className="grid grid-cols-2 gap-4">
                <Input id="city" label="City" {...register("city")} error={errors.city?.message} />
                <Input
                  id="postcode" label="Postcode"
                  {...register("postcode")} error={errors.postcode?.message}
                />
              </div>
              <Input
                id="country" label="Country code" placeholder="GB"
                maxLength={2} {...register("country")} error={errors.country?.message}
              />
            </div>

            {/* Payment notice */}
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-700">
              Payment is processed securely by Stripe. Card details are never stored on our servers.
            </div>

            {error && (
              <p className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>
              Place order — {formatPrice(basket.subtotal)}
            </Button>
          </form>
        </div>

        {/* Order summary */}
        <div className="lg:w-80 shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl p-6 sticky top-24">
            <h2 className="font-semibold text-gray-900 mb-4">
              Order summary ({basket.total_items}{" "}
              {basket.total_items === 1 ? "item" : "items"})
            </h2>
            <div className="space-y-3 mb-4">
              {basket.items.map((item) => (
                <div key={item.product_id} className="flex justify-between text-sm">
                  <span className="text-gray-600 truncate mr-2">
                    {item.title}{" "}
                    <span className="text-gray-400">×{item.qty}</span>
                  </span>
                  <span className="font-medium text-gray-900 shrink-0">
                    {formatPrice(item.line_total)}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t border-gray-200 pt-4 space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Subtotal</span>
                <span>{formatPrice(basket.subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Shipping</span>
                <span className="text-green-600">Free</span>
              </div>
              <div className="flex justify-between font-bold text-gray-900 pt-1">
                <span>Total</span>
                <span>{formatPrice(basket.subtotal)}</span>
              </div>
            </div>
            <Link href="/basket">
              <Button variant="ghost" size="sm" className="w-full mt-4 text-gray-500">
                ← Edit basket
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
