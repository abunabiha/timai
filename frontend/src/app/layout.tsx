import "./globals.css";
import React from "react";
import { I18nProvider } from "@/lib/i18n";
import { ThemeProvider } from "@/lib/theme";

export const metadata = {
  title: "TimAI - Platform Tim Agen AI Berbasis Scrum",
  description: "Platform kolaborasi tim agen AI otonom berbasis kerangka kerja Scrum.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors">
        <ThemeProvider>
          <I18nProvider>{children}</I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
