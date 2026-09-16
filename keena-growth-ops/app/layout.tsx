import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Keena Growth Ops",
  description: "A weekly, real-data healthcare sales pipeline for Keena Health, sourced from open RFPs and job postings.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
