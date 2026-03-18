"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { LayoutDashboard, ShoppingBag, User, LogOut } from "lucide-react";

const NAV = [
  { href: "/account", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/account/orders", label: "Orders", icon: ShoppingBag },
  { href: "/account/profile", label: "Profile", icon: User },
];

export default function AccountLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout, _hasHydrated } = useAuthStore();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!_hasHydrated) return;
    // Mark that we've done the auth check
    setChecked(true);
    if (!isAuthenticated) {
      router.replace(`/login?next=${pathname}`);
    }
  }, [_hasHydrated, isAuthenticated]);

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  // Show skeleton while waiting for hydration check
  if (!checked) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col md:flex-row gap-8">
          <aside className="md:w-56 shrink-0">
            <div className="bg-gray-100 rounded-xl h-48 animate-pulse" />
          </aside>
          <div className="flex-1 space-y-4">
            <div className="bg-gray-100 rounded-xl h-32 animate-pulse" />
            <div className="bg-gray-100 rounded-xl h-32 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  // After check — not logged in, redirect is happening
  if (!isAuthenticated) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar */}
        <aside className="md:w-56 shrink-0">
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-4 py-4 bg-gray-50 border-b border-gray-200">
              <p className="font-semibold text-gray-900 truncate">
                {user?.full_name || user?.user_name || "Account"}
              </p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
            <nav className="py-2">
              {NAV.map(({ href, label, icon: Icon, exact }) => {
                const active = exact
                  ? pathname === href
                  : pathname.startsWith(href);
                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                      active
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <Icon size={16} />
                    {label}
                  </Link>
                );
              })}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors"
              >
                <LogOut size={16} />
                Sign out
              </button>
            </nav>
          </div>
        </aside>

        {/* Content */}
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </div>
  );
}
