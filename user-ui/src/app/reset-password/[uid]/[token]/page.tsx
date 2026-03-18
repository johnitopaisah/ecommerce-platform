"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/services";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const schema = z
  .object({
    new_password: z.string().min(8, "At least 8 characters"),
    new_password2: z.string().min(1, "Confirm your password"),
  })
  .refine((d) => d.new_password === d.new_password2, {
    message: "Passwords do not match",
    path: ["new_password2"],
  });

type FormData = z.infer<typeof schema>;

export default function ResetPasswordConfirmPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const router = useRouter();
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await authApi.passwordResetConfirm({
        uid,
        token,
        new_password: data.new_password,
        new_password2: data.new_password2,
      });
      setSuccess(true);
    } catch (err: any) {
      setError("root", {
        message: err?.response?.data?.detail || "Reset failed. The link may be expired.",
      });
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
          <h1 className="text-xl font-bold text-gray-900 mb-2">Password reset!</h1>
          <p className="text-gray-500 text-sm mb-6">
            Your password has been updated. You can now sign in with your new password.
          </p>
          <Link href="/login">
            <Button className="w-full">Sign in</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Set new password</h1>
          <p className="text-sm text-gray-500 mb-8">Enter your new password below.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              id="new_password"
              label="New password"
              type="password"
              placeholder="Min. 8 characters"
              {...register("new_password")}
              error={errors.new_password?.message}
            />
            <Input
              id="new_password2"
              label="Confirm new password"
              type="password"
              placeholder="Repeat password"
              {...register("new_password2")}
              error={errors.new_password2?.message}
            />

            {errors.root && (
              <p className="text-sm text-red-500 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {errors.root.message}
              </p>
            )}

            <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>
              Reset password
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
