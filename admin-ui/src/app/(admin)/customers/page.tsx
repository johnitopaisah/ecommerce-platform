"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, CheckCircle, XCircle, UserX } from "lucide-react";
import { customersApi, usersApi } from "@/lib/services";
import type { User } from "@/types";
import { formatDate } from "@/lib/utils";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "inactive">("all");

  const fetchCustomers = useCallback(async (currentFilter: string, currentSearch: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (currentFilter === "active") params.is_active = "true";
      if (currentFilter === "inactive") params.is_active = "false";
      if (currentSearch) params.search = currentSearch;
      const res = await customersApi.list(params);
      setCustomers(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchCustomers(filter, "");
  }, [filter, fetchCustomers]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    void fetchCustomers(filter, search);
  };

  const handleDeactivate = async (customer: User) => {
    if (!confirm(`Deactivate ${customer.email}?`)) return;
    await usersApi.deactivate(customer.id);
    setCustomers((prev) => prev.map((c) => c.id === customer.id ? { ...c, is_active: false } : c));
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
        <p className="text-sm text-gray-500 mt-0.5">{customers.length} customer{customers.length === 1 ? "" : "s"}</p>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
          {(["all", "active", "inactive"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors capitalize ${
                filter === f ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <form onSubmit={handleSearch} className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by email or username…"
            className="pl-8 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 w-64"
          />
        </form>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading customers…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {["Customer", "Username", "Active", "Joined", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{customer.full_name || "—"}</p>
                      <p className="text-xs text-gray-400">{customer.email}</p>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{customer.user_name}</td>
                    <td className="px-4 py-3">
                      {customer.is_active
                        ? <CheckCircle size={15} className="text-green-500" />
                        : <XCircle size={15} className="text-gray-300" />}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(customer.created)}</td>
                    <td className="px-4 py-3">
                      {customer.is_active && (
                        <button
                          onClick={() => handleDeactivate(customer)}
                          title="Deactivate customer"
                          className="p-1.5 rounded-lg text-gray-400 hover:text-danger-600 hover:bg-danger-50 transition-colors"
                        >
                          <UserX size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {!customers.length && (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-sm text-gray-400">No customers found.</td>
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
