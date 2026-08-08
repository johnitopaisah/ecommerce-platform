"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Package, Tag, ShoppingBag, Users,
  LogOut, ChevronRight, ChevronsLeft, ChevronsRight,
  Store, ShieldCheck, Star, Percent,
  UserCog, KeyRound, ClipboardCheck, ScrollText,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { rbacApi } from "@/lib/services";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  badgeKey?: "pendingRequests";
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    label: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Catalog",
    items: [
      { href: "/products", label: "Products", icon: Package },
      { href: "/categories", label: "Categories", icon: Tag },
    ],
  },
  {
    label: "Sales",
    items: [
      { href: "/orders", label: "Orders", icon: ShoppingBag },
      { href: "/coupons", label: "Coupons", icon: Percent },
      { href: "/reviews", label: "Reviews", icon: Star },
    ],
  },
  {
    label: "People",
    items: [{ href: "/customers", label: "Customers", icon: Users }],
  },
  {
    // Deliberately separate from "People" — customers and team members are
    // different audiences with different information needs, not one list
    // with a filter toggle. See the RBAC design notes.
    label: "Organization",
    items: [
      { href: "/team", label: "Team Members", icon: UserCog },
      { href: "/roles", label: "Roles", icon: KeyRound },
      { href: "/access-requests", label: "Access Requests", icon: ClipboardCheck, badgeKey: "pendingRequests" },
      { href: "/audit-log", label: "Audit Log", icon: ScrollText },
    ],
  },
];

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);
  const [pendingRequestCount, setPendingRequestCount] = useState(0);

  useEffect(() => {
    rbacApi.pendingRequests()
      .then((res) => setPendingRequestCount(res.data.length))
      .catch(() => {});
  }, [pathname]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const displayName = user?.full_name?.trim() || user?.user_name || "Admin";

  return (
    <aside
      className={cn(
        "shrink-0 bg-gray-900 text-white flex flex-col min-h-screen transition-all duration-200",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* Logo */}
      <div className={cn("flex items-center border-b border-gray-800 px-4 py-5", collapsed && "justify-center px-2")}>
        <div className="w-8 h-8 rounded-lg bg-white text-gray-900 flex items-center justify-center font-bold text-sm shrink-0">
          S
        </div>
        {!collapsed && (
          <div className="ml-3 min-w-0">
            <p className="text-sm font-bold leading-tight truncate">ShopNow</p>
            <p className="text-[11px] text-gray-400 leading-tight">Admin Panel</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {SECTIONS.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                {section.label}
              </p>
            )}
            <div className="space-y-1">
              {section.items.map(({ href, label, icon: Icon, badgeKey }) => {
                const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
                const badgeCount = badgeKey === "pendingRequests" ? pendingRequestCount : 0;
                return (
                  <Link
                    key={href}
                    href={href}
                    title={collapsed ? label : undefined}
                    className={cn(
                      "relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                      collapsed && "justify-center px-0",
                      active
                        ? "bg-white/10 text-white"
                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <Icon size={17} className="shrink-0" />
                    {!collapsed && (
                      <>
                        <span className="truncate">{label}</span>
                        {badgeCount > 0 && (
                          <span className="ml-auto bg-amber-500 text-white text-[10px] font-bold rounded-full min-w-4.5 h-4.5 flex items-center justify-center px-1 shrink-0">
                            {badgeCount > 99 ? "99+" : badgeCount}
                          </span>
                        )}
                        {active && badgeCount === 0 && <ChevronRight size={14} className="ml-auto opacity-60 shrink-0" />}
                      </>
                    )}
                    {collapsed && badgeCount > 0 && (
                      <span className="absolute top-1 right-1 w-2 h-2 bg-amber-500 rounded-full" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* View storefront */}
      <div className="px-3 pb-2">
        <a
          href="/"
          target="_blank"
          rel="noopener noreferrer"
          title={collapsed ? "View storefront" : undefined}
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:bg-white/5 hover:text-white transition-colors border border-dashed border-gray-800",
            collapsed && "justify-center px-0"
          )}
        >
          <Store size={17} className="shrink-0" />
          {!collapsed && <span className="truncate">View storefront</span>}
        </a>
      </div>

      {/* Collapse toggle */}
      <div className="px-3 pb-2">
        <button
          onClick={() => setCollapsed((v) => !v)}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-gray-500 hover:bg-white/5 hover:text-gray-300 transition-colors",
            collapsed && "justify-center px-0"
          )}
        >
          {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
          {!collapsed && "Collapse"}
        </button>
      </div>

      {/* User + logout */}
      <div className="px-3 py-4 border-t border-gray-800">
        <div className={cn("flex items-center gap-3 px-3 py-2 mb-2", collapsed && "justify-center px-0")}>
          <div className="w-8 h-8 rounded-full bg-gray-700 text-white flex items-center justify-center text-xs font-semibold shrink-0">
            {initials(displayName)}
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-medium text-white truncate">{displayName}</p>
              </div>
              <p className="text-[11px] text-gray-400 truncate flex items-center gap-1">
                <ShieldCheck size={11} className="shrink-0" />
                Administrator
              </p>
            </div>
          )}
        </div>
        <button
          onClick={handleLogout}
          title={collapsed ? "Sign out" : undefined}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-white/5 hover:text-white transition-colors",
            collapsed && "justify-center px-0"
          )}
        >
          <LogOut size={17} className="shrink-0" />
          {!collapsed && "Sign out"}
        </button>
      </div>
    </aside>
  );
}
