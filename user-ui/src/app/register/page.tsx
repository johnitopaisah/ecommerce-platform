"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { authApi } from "@/lib/services";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const schema = z
  .object({
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    user_name: z.string().min(4, "Username must be at least 4 characters"),
    email: z.string().email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    password2: z.string().min(1, "Please confirm your password"),
  })
  .refine((d) => d.password === d.password2, {
    message: "Passwords do not match",
    path: ["password2"],
  });

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const [success, setSuccess] = useState(false);

  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await authApi.register(data);
      setSuccess(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; errors?: Record<string, string[]> } } };
      const errData = e?.response?.data;
      if (errData?.errors) {
        Object.entries(errData.errors).forEach(([field, messages]) => {
          setError(field as keyof FormData, {
            message: Array.isArray(messages) ? messages[0] : String(messages),
          });
        });
      } else {
        setError("root", { message: errData?.detail || "Registration failed. Please try again." });
      }
    }
  };

  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Check your email</h1>
          <p className="text-gray-500 text-sm mb-6">
            We sent an activation link to your email. Click it to activate your account.
          </p>
          <Link href="/login">
            <Button variant="outline" className="w-full">Back to sign in</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Create account</h1>
          <p className="text-sm text-gray-500 mb-8">
            Already have an account?{" "}
            <Link href="/login" className="text-gray-900 font-medium hover:underline">Sign in</Link>
          </p>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input id="first_name" label="First name" placeholder="John"
                {...register("first_name")} error={errors.first_name?.message} />
              <Input id="last_name" label="Last name" placeholder="Doe"
                {...register("last_name")} error={errors.last_name?.message} />
            </div>
            <Input id="user_name" label="Username" placeholder="johndoe" autoComplete="username"
              {...register("user_name")} error={errors.user_name?.message} />
            <Input id="email" label="Email address" type="email" placeholder="you@example.com"
              autoComplete="email" {...register("email")} error={errors.email?.message} />
            <Input id="password" label="Password" type="password" placeholder="Min. 8 characters"
              autoComplete="new-password" {...register("password")} error={errors.password?.message} />
            <Input id="password2" label="Confirm password" type="password" placeholder="Repeat password"
              autoComplete="new-password" {...register("password2")} error={errors.password2?.message} />
            {errors.root && (
              <p className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {errors.root.message}
              </p>
            )}
            <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>Create account</Button>
          </form>
        </div>
      </div>
    </div>
  );
}
