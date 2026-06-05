import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";

import { DataBootstrap } from "@/components/DataBootstrap";
import { ToasterProvider } from "@/components/ui/toaster";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "FlyOS — Pretty Fly Commerce OS",
  description: "Find stuck cash in inventory, POs, and ad spend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[#0a0a0a] antialiased">
        <ToasterProvider>
          <DataBootstrap />
          <div className="mx-auto max-w-[1400px]">{children}</div>
        </ToasterProvider>
      </body>
    </html>
  );
}
