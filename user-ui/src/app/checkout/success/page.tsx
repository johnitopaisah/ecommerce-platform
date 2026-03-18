import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function CheckoutSuccessPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Order placed!</h1>
        <p className="text-gray-500 mb-8">
          Thank you for your order. We'll send a confirmation to your email shortly.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/account/orders">
            <Button size="lg">View my orders</Button>
          </Link>
          <Link href="/products">
            <Button size="lg" variant="outline">Continue shopping</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
