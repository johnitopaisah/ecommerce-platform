"use client";

import { useEffect, useState } from "react";
import { BadgeCheck } from "lucide-react";
import { reviewsApi } from "@/lib/services";
import { useAuthStore } from "@/store/authStore";
import { useToastStore } from "@/store/toastStore";
import StarRating from "@/components/ui/StarRating";
import { Button } from "@/components/ui/Button";
import type { Review } from "@/types";

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export default function ProductReviews({ productSlug }: { productSlug: string }) {
  const { isAuthenticated } = useAuthStore();
  const { show } = useToastStore();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    reviewsApi.list(productSlug)
      .then((r) => setReviews(r.data))
      .finally(() => setLoading(false));
  }, [productSlug]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) {
      show("Please select a star rating.", "error");
      return;
    }
    setSubmitting(true);
    try {
      await reviewsApi.create(productSlug, { rating, comment });
      setSubmitted(true);
      show("Thanks! Your review will appear once approved.", "success");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      show(err?.response?.data?.detail || "Couldn't submit your review.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mt-14 border-t border-gray-100 pt-10">
      <h2 className="text-xl font-bold text-gray-900 mb-6">
        Reviews {reviews.length > 0 && <span className="text-gray-400 font-normal">({reviews.length})</span>}
      </h2>

      {isAuthenticated && !submitted && (
        <form onSubmit={handleSubmit} className="mb-8 p-5 bg-white border border-gray-200 rounded-xl max-w-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">Leave a review</p>
          <StarRating value={rating} onChange={setRating} size={22} className="mb-3" />
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your thoughts about this product…"
            rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 resize-none mb-3"
          />
          <Button type="submit" size="sm" isLoading={submitting}>Submit review</Button>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-gray-400">Loading reviews…</p>
      ) : reviews.length === 0 ? (
        <p className="text-sm text-gray-400">No reviews yet — be the first to share your thoughts.</p>
      ) : (
        <div className="space-y-5 max-w-2xl">
          {reviews.map((review) => (
            <div key={review.id} className="border-b border-gray-100 pb-5">
              <div className="flex items-center gap-2 mb-1">
                <StarRating value={review.rating} size={14} />
                <span className="text-sm font-medium text-gray-900">{review.reviewer_name}</span>
                {review.verified_purchase && (
                  <span className="flex items-center gap-1 text-xs text-success-700 bg-success-50 px-2 py-0.5 rounded-full">
                    <BadgeCheck size={12} />
                    Verified purchase
                  </span>
                )}
              </div>
              {review.title && <p className="text-sm font-medium text-gray-800">{review.title}</p>}
              {review.comment && <p className="text-sm text-gray-600 mt-1">{review.comment}</p>}
              <p className="text-xs text-gray-400 mt-1">{formatDate(review.created)}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
