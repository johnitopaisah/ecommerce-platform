import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import AppBootstrap from "@/components/AppBootstrap";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: { default: "ShopNow", template: "%s | ShopNow" },
  description: "Your one-stop shop for quality products.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={geist.variable} suppressHydrationWarning>
      <body className="min-h-screen flex flex-col bg-gray-50 antialiased font-sans">
        <AppBootstrap>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </AppBootstrap>
      </body>
    </html>
  );
}
