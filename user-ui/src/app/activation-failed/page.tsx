import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function ActivationFailedPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
        <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-7 h-7 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Activation link invalid</h1>
        <p className="text-gray-500 text-sm mb-6">
          This activation link is invalid or has already been used.
          Links expire after 24 hours. Please register again to get a new link.
        </p>
        <div className="flex flex-col gap-3">
          <Link href="/register">
            <Button className="w-full">Register again</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" className="w-full">Sign in</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
