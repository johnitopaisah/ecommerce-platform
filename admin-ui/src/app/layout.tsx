import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import AdminBootstrap from "@/components/AdminBootstrap";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: { default: "Admin — ShopNow", template: "%s | Admin" },
  description: "ShopNow administration panel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={geist.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 antialiased font-sans">
        <AdminBootstrap>{children}</AdminBootstrap>
      </body>
    </html>
  );
}
