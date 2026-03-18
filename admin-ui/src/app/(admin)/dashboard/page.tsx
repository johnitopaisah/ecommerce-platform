"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  Users, Package, ShoppingBag, TrendingUp, AlertTriangle, XCircle,
} from "lucide-react";
import { statsApi } from "@/lib/services";
import { StatCard } from "@/components/ui/StatCard";
import { formatPrice } from "@/lib/utils";
import type { AdminStats } from "@/types";
import type { AxiosResponse } from "axios";

export default function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statsApi.get()
      .then((r: AxiosResponse<AdminStats>) => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-24 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!stats) return <p className="text-gray-500">Failed to load stats.</p>;

  const orderData = [
    { name: "Total", value: stats.orders.total },
    { name: "Today", value: stats.orders.today },
    { name: "Pending", value: stats.orders.pending },
  ];

  const productData = [
    { name: "Active", value: stats.products.total_active, color: "#111827" },
    { name: "Low stock", value: stats.products.low_stock, color: "#f59e0b" },
    { name: "Out of stock", value: stats.products.out_of_stock, color: "#ef4444" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Platform overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total users"
          value={stats.users.total}
          sub={`${stats.users.active} active · ${stats.users.new_today} new today`}
          icon={<Users size={20} className="text-gray-700" />}
          color="bg-gray-100"
        />
        <StatCard
          label="Active products"
          value={stats.products.total_active}
          sub={`${stats.products.low_stock} low stock`}
          icon={<Package size={20} className="text-blue-700" />}
          color="bg-blue-50"
        />
        <StatCard
          label="Total orders"
          value={stats.orders.total}
          sub={`${stats.orders.pending} pending`}
          icon={<ShoppingBag size={20} className="text-purple-700" />}
          color="bg-purple-50"
        />
        <StatCard
          label="Revenue (30 days)"
          value={formatPrice(stats.revenue.last_30_days)}
          sub={`Confirmed: ${formatPrice(stats.revenue.confirmed_total)}`}
          icon={<TrendingUp size={20} className="text-green-700" />}
          color="bg-green-50"
        />
      </div>

      {(stats.products.low_stock > 0 || stats.products.out_of_stock > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {stats.products.low_stock > 0 && (
            <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              <AlertTriangle size={18} className="text-amber-600 shrink-0" />
              <p className="text-sm text-amber-800">
                <span className="font-semibold">{stats.products.low_stock}</span> products are low on stock
              </p>
            </div>
          )}
          {stats.products.out_of_stock > 0 && (
            <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              <XCircle size={18} className="text-red-500 shrink-0" />
              <p className="text-sm text-red-700">
                <span className="font-semibold">{stats.products.out_of_stock}</span> products are out of stock
              </p>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Orders overview</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={orderData} barCategoryGap="40%">
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", fontSize: 12 }} />
              <Bar dataKey="value" fill="#111827" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Product stock status</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={productData}
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={90}
                paddingAngle={3} dataKey="value"
                label={({ name, value }: { name: string; value: number }) => `${name}: ${value}`}
                labelLine={false}
              >
                {productData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Legend
                iconType="circle" iconSize={8}
                formatter={(value: string) => (
                  <span style={{ fontSize: 12, color: "#374151" }}>{value}</span>
                )}
              />
              <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="font-semibold text-gray-900 mb-4">Revenue</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div>
            <p className="text-xs text-gray-500 mb-1">Last 30 days (all orders)</p>
            <p className="text-2xl font-bold text-gray-900">{formatPrice(stats.revenue.last_30_days)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">All time (all orders)</p>
            <p className="text-2xl font-bold text-gray-900">{formatPrice(stats.revenue.total)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Stripe confirmed</p>
            <p className="text-2xl font-bold text-green-700">{formatPrice(stats.revenue.confirmed_total)}</p>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-4">
          "All orders" includes pending orders awaiting payment.
          "Stripe confirmed" shows only webhook-confirmed payments.
        </p>
      </div>
    </div>
  );
}
