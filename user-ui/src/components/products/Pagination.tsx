import Link from "next/link";

interface PaginationProps {
  currentPage: number;
  totalCount: number;
  pageSize: number;
  basePath: string;
  searchParams: Record<string, string | undefined>;
}

export default function Pagination({
  currentPage,
  totalCount,
  pageSize,
  basePath,
  searchParams,
}: PaginationProps) {
  const totalPages = Math.ceil(totalCount / pageSize);
  if (totalPages <= 1) return null;

  const buildHref = (page: number) => {
    const params = new URLSearchParams();
    Object.entries(searchParams).forEach(([k, v]) => {
      if (v && k !== "page") params.set(k, v);
    });
    if (page > 1) params.set("page", String(page));
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const arrowClass = (disabled: boolean) =>
    `px-3 py-1.5 text-sm rounded-lg border transition-colors ${
      disabled
        ? "pointer-events-none text-gray-300 border-gray-200"
        : "text-gray-600 border-gray-300 hover:bg-gray-50"
    }`;

  return (
    <nav className="flex items-center justify-center gap-1 mt-10" aria-label="Pagination">
      <Link href={buildHref(Math.max(1, currentPage - 1))} className={arrowClass(currentPage === 1)}>
        Previous
      </Link>
      {start > 1 && <span className="px-2 text-gray-400">…</span>}
      {pages.map((p) => (
        <Link
          key={p}
          href={buildHref(p)}
          className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
            p === currentPage
              ? "bg-gray-900 text-white border-gray-900"
              : "text-gray-600 border-gray-300 hover:bg-gray-50"
          }`}
        >
          {p}
        </Link>
      ))}
      {end < totalPages && <span className="px-2 text-gray-400">…</span>}
      <Link
        href={buildHref(Math.min(totalPages, currentPage + 1))}
        className={arrowClass(currentPage === totalPages)}
      >
        Next
      </Link>
    </nav>
  );
}
