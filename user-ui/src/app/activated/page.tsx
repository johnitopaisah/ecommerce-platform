"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

// Inner component that uses useSearchParams — must be inside Suspense
function ActivatedContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setTokens, fetchMe } = useAuthStore();
  const { mergeBasket } = useBasketStore();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const activate = async () => {
      const access = searchParams.get("access");
      const refresh = searchParams.get("refresh");

      if (!access || !refresh) {
        setStatus("error");
        return;
      }

      try {
        setTokens(access, refresh);
        document.cookie = "is_authenticated=1; path=/; max-age=604800; SameSite=Lax";
        await fetchMe();
        await mergeBasket();
        setStatus("success");
        setTimeout(() => router.push("/account"), 2000);
      } catch {
        setStatus("error");
      }
    };

    void activate();
  }, [fetchMe, mergeBasket, router, searchParams, setTokens]);

  if (status === "loading") {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-900 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Activating your account…</p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Activation failed</h1>
          <p className="text-gray-500 text-sm mb-6">
            Something went wrong. The link may be invalid or expired.
          </p>
          <Link href="/register">
            <Button className="w-full">Register again</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
        <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Account activated!</h1>
        <p className="text-gray-500 text-sm mb-2">
          Welcome to ShopNow. You&apos;re now logged in.
        </p>
        <p className="text-xs text-gray-400">Redirecting to your dashboard…</p>
      </div>
    </div>
  );
}

export default function ActivatedPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-gray-300 border-t-gray-900 rounded-full animate-spin" />
      </div>
    }>
      <ActivatedContent />
    </Suspense>
  );
}
