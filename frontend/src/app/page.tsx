"use client";

import React from "react";
import { useI18n } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";
import { Moon, Sun, Globe, PlusCircle, Layers, CheckSquare, MessageSquare, BookOpen, Settings } from "lucide-react";

export default function HomePage() {
  const { t, locale, setLocale } = useI18n();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              T
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
                {t.appName}
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                v1.0 (Scrum AI)
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
            <span className="text-indigo-600 dark:text-indigo-400 cursor-pointer flex items-center gap-1.5">
              <Layers className="w-4 h-4" /> {t.dashboard}
            </span>
            <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
              <CheckSquare className="w-4 h-4" /> {t.confirmations}
            </span>
            <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
              <MessageSquare className="w-4 h-4" /> {t.teamRoom}
            </span>
            <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" /> {t.systemLearning}
            </span>
            <span className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer flex items-center gap-1.5">
              <Settings className="w-4 h-4" /> {t.settings}
            </span>
          </nav>

          <div className="flex items-center space-x-2">
            {/* Language Switcher */}
            <button
              onClick={() => setLocale(locale === "id" ? "en" : "id")}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center gap-1 text-xs font-semibold"
              title={t.switchLang}
            >
              <Globe className="w-4 h-4" />
              <span>{locale.toUpperCase()}</span>
            </button>

            {/* Dark/Light Mode Switcher */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              title={t.switchTheme}
            >
              {theme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col justify-center">
        <div className="text-center max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
            {t.tagline}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {t.welcomeTitle}
          </h1>
          <p className="text-base text-slate-600 dark:text-slate-300 leading-relaxed">
            {t.welcomeSubtitle}
          </p>

          <div className="pt-8">
            <div className="p-8 border-2 border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/50 dark:bg-slate-950/40 space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center text-slate-400">
                <Layers className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
                {t.emptyStateTitle}
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                {t.emptyStateDesc}
              </p>
              <div className="pt-2">
                <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm shadow-sm transition-colors">
                  <PlusCircle className="w-4 h-4" />
                  {t.createProject}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-xs text-slate-500 dark:text-slate-400">
        <p>TimAI &copy; 2026 &bull; {t.tagline}</p>
      </footer>
    </div>
  );
}
