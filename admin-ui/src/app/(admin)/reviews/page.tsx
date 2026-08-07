"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, X, Trash2, BadgeCheck } from "lucide-react";
import { reviewsApi } from "@/lib/services";
import { formatDate } from "@/lib/utils";
import { useToastStore } from "@/store/toastStore";
import StarRating from "@/components/ui/StarRating";
import type { Review } from "@/types";

const FILTERS = [
  { label: "Pending", value: "pending" as const },
  { label: "Approved", value: "approved" as const },
  { label: "All", value: "all" as const },
];

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"pending" | "approved" | "all">("pending");
  const { show } = useToastStore();

  const load = useCallback(async (f: typeof filter) => {
    setLoading(true);
    try {
      const isApproved = f === "all" ? undefined : f === "approved";
      const res = await reviewsApi.list(isApproved);
      setReviews(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(filter); }, [filter, load]);

  const handleApprove = async (review: Review) => {
    await reviewsApi.approve(review.id);
    show(`Review approved.`, "success");
    void load(filter);
  };

  const handleReject = async (review: Review) => {
    await reviewsApi.reject(review.id);
    show(`Review rejected.`, "info");
    void load(filter);
  };

  const handleDelete = async (review: Review) => {
    if (!confirm("Permanently delete this review?")) return;
    await reviewsApi.delete(review.id);
    show(`Review deleted.`, "success");
    void load(filter);
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reviews</h1>
        <p className="text-sm text-gray-500 mt-0.5">{reviews.length} review{reviews.length === 1 ? "" : "s"}</p>
      </div>

      <div className="flex bg-gray-100 rounded-lg p-1 gap-1 w-fit">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              filter === f.value ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {["Product", "Reviewer", "Rating", "Review", "Date", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reviews.map((review) => (
                  <tr key={review.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{review.product_title}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className="text-gray-600 text-xs">{review.reviewer_email}</span>
                        {review.verified_purchase && (
                          <BadgeCheck size={13} className="text-success-600 shrink-0" />
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3"><StarRating value={review.rating} /></td>
                    <td className="px-4 py-3 max-w-xs">
                      {review.title && <p className="font-medium text-gray-800 text-xs">{review.title}</p>}
                      <p className="text-gray-500 text-xs line-clamp-2">{review.comment || "—"}</p>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(review.created)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        {!review.is_approved && (
                          <button onClick={() => handleApprove(review)} title="Approve"
                            className="p-1.5 rounded-lg text-success-600 hover:bg-success-50">
                            <Check size={15} />
                          </button>
                        )}
                        {review.is_approved && (
                          <button onClick={() => handleReject(review)} title="Unpublish"
                            className="p-1.5 rounded-lg text-warning-600 hover:bg-warning-50">
                            <X size={15} />
                          </button>
                        )}
                        <button onClick={() => handleDelete(review)} title="Delete"
                          className="p-1.5 rounded-lg text-danger-600 hover:bg-danger-50">
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!reviews.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-sm text-gray-400">
                      {filter === "pending" ? "No reviews awaiting moderation." : "No reviews found."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
