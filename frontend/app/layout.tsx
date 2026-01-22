import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Intent Advisor | Smart Financial Guidance",
  description:
    "Your intelligent financial advisor powered by AI. Get personalized product recommendations and investment guidance.",
  keywords: ["financial advisor", "AI", "investment", "retirement planning"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full antialiased">{children}</body>
    </html>
  );
}
