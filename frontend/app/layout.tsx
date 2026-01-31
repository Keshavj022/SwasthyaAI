import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hospital AI System",
  description: "Offline-first healthcare AI with clinical decision support",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50">
        {children}
      </body>
    </html>
  );
}
