"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/services";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
});

type FormData = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await authApi.passwordReset(data.email);
    } finally {
      // Always show success to avoid email enumeration
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-xl font-bold text-gray-900 mb-2">Check your email</h1>
          <p className="text-gray-500 text-sm mb-6">
            If that email address exists in our system, we've sent a password reset link.
          </p>
          <Link href="/login">
            <Button variant="outline" className="w-full">Back to sign in</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Reset password</h1>
          <p className="text-sm text-gray-500 mb-8">
            Enter your email and we'll send a reset link.
          </p>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              id="email"
              label="Email address"
              type="email"
              placeholder="you@example.com"
              {...register("email")}
              error={errors.email?.message}
            />
            <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>
              Send reset link
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Link href="/login" className="text-sm text-gray-500 hover:underline">
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
