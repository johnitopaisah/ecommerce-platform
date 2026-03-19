"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/authStore";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();

  const { register, handleSubmit, setError, formState: { errors } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await login(data.email, data.password);
      router.push("/");
    } catch (err: unknown) {
      const e = err as { message?: string; response?: { data?: { detail?: string } } };
      setError("root", {
        message: e?.response?.data?.detail || e?.message || "Login failed.",
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">ShopNow</h1>
          <p className="text-gray-400 text-sm mt-1">Admin Panel</p>
        </div>
        <div className="bg-white rounded-2xl p-8 shadow-xl">
          <h2 className="text-lg font-bold text-gray-900 mb-6">Sign in to continue</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input id="email" label="Email address" type="email" placeholder="admin@example.com"
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
        </div>
      </div>
    </div>
  );
}
