"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShoppingCart, User, Menu, X, Search } from "lucide-react";
import { useState, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useBasketStore } from "@/store/basketStore";

export default function Navbar() {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuthStore();
  const { basket, fetchBasket } = useBasketStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => { fetchBasket(); }, [fetchBasket]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (search.trim()) {
      router.push(`/products?search=${encodeURIComponent(search.trim())}`);
      setSearch("");
    }
  };

  const handleLogout = async () => {
    await logout();
    setUserMenuOpen(false);
    document.cookie = "is_authenticated=; max-age=0; path=/";
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          <Link href="/" className="text-xl font-bold text-gray-900 shrink-0">ShopNow</Link>

          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-md">
            <div className="relative w-full">
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products…"
                className="w-full pl-4 pr-10 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900" />
              <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                <Search size={18} />
              </button>
            </div>
          </form>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-600">
            <Link href="/products" className="hover:text-gray-900 transition-colors">Products</Link>
            <Link href="/categories" className="hover:text-gray-900 transition-colors">Categories</Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/basket" className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors">
              <ShoppingCart size={22} />
              {basket.total_items > 0 && (
                <span className="absolute -top-1 -right-1 bg-gray-900 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {basket.total_items > 99 ? "99+" : basket.total_items}
                </span>
              )}
            </Link>

            <div className="relative">
              <button onClick={() => setUserMenuOpen((v) => !v)} className="p-2 text-gray-600 hover:text-gray-900 transition-colors">
                <User size={22} />
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-1 z-50">
                  {isAuthenticated ? (
                    <>
                      <p className="px-4 py-2 text-xs text-gray-500 truncate">{user?.email}</p>
                      <hr className="border-gray-100 my-1" />
                      <Link href="/account" onClick={() => setUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Dashboard</Link>
                      <Link href="/account/profile" onClick={() => setUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Profile</Link>
                      <Link href="/account/orders" onClick={() => setUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Orders</Link>
                      <hr className="border-gray-100 my-1" />
                      <button onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">Sign out</button>
                    </>
                  ) : (
                    <>
                      <Link href="/login" onClick={() => setUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Sign in</Link>
                      <Link href="/register" onClick={() => setUserMenuOpen(false)}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Create account</Link>
                    </>
                  )}
                </div>
              )}
            </div>

            <button onClick={() => setMenuOpen((v) => !v)} className="md:hidden p-2 text-gray-600 hover:text-gray-900">
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="md:hidden py-4 border-t border-gray-100 space-y-3">
            <form onSubmit={handleSearch} className="relative">
              <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products…"
                className="w-full pl-4 pr-10 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900" />
              <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400">
                <Search size={18} />
              </button>
            </form>
            <Link href="/products" onClick={() => setMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Products</Link>
            <Link href="/categories" onClick={() => setMenuOpen(false)}
              className="block py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Categories</Link>
          </div>
        )}
      </div>
    </header>
  );
}
