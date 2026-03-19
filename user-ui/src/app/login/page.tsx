"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

function setAuthCookie() {
  document.cookie = "is_authenticated=1; path=/; max-age=604800; SameSite=Lax";
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/account";
  const { login, isLoading } = useAuthStore();
  const { mergeBasket } = useBasketStore();

  const { register, handleSubmit, setError, formState: { errors } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.email, data.password);
      setAuthCookie();
      await mergeBasket();
      await new Promise((r) => setTimeout(r, 100));
      router.replace(next);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; error?: string } } };
      setError("root", {
        message: e?.response?.data?.detail || e?.response?.data?.error || "Invalid email or password.",
      });
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Sign in</h1>
          <p className="text-sm text-gray-500 mb-8">
            New here?{" "}
            <Link href="/register" className="text-gray-900 font-medium hover:underline">
              Create an account
            </Link>
          </p>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input id="email" label="Email address" type="email" placeholder="you@example.com"
              autoComplete="email" {...register("email")} error={errors.email?.message} />
            <Input id="password" label="Password" type="password" placeholder="••••••••"
              autoComplete="current-password" {...register("password")} error={errors.password?.message} />
            {errors.root && (
              <p className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {errors.root.message}
              </p>
            )}
            <Button type="submit" size="lg" className="w-full" isLoading={isLoading}>Sign in</Button>
          </form>
          <div className="mt-4 text-center">
            <Link href="/reset-password" className="text-sm text-gray-500 hover:text-gray-900 hover:underline">
              Forgot your password?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
