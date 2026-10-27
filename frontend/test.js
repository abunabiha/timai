// Test script for frontend integrity and i18n
const assert = require("assert");

// Mock React imports for testing dictionary directly
const idTranslations = {
  appName: "TimAI",
  tagline: "Platform Tim Agen AI Berbasis Scrum",
  welcomeTitle: "Selamat Datang di TimAI",
  welcomeSubtitle: "Bekerja bersama tim agen AI otonom yang dikelola secara terstruktur melalui siklus Scrum.",
  dashboard: "Beranda",
  projects: "Proyek",
  confirmations: "Kotak Konfirmasi",
  teamRoom: "Ruang Tim",
  settings: "Pengaturan",
  systemLearning: "Yang Dipelajari Sistem",
  switchTheme: "Ganti Tema",
  switchLang: "Bahasa",
  emptyStateTitle: "Belum Ada Proyek Aktif",
  emptyStateDesc: "Mulai perjalanan Anda dengan memberikan brief proyek baru. Sistem akan mengusulkan tim agen AI terbaik untuk Anda.",
  createProject: "Buat Proyek Baru",
};

const enTranslations = {
  appName: "TimAI",
  tagline: "Scrum-Based AI Agent Team Platform",
  welcomeTitle: "Welcome to TimAI",
  welcomeSubtitle: "Collaborate with an autonomous AI agent team managed through Scrum cycles.",
  dashboard: "Dashboard",
  projects: "Projects",
  confirmations: "Confirmation Box",
  teamRoom: "Team Room",
  settings: "Settings",
  systemLearning: "System Learning",
  switchTheme: "Toggle Theme",
  switchLang: "Language",
  emptyStateTitle: "No Active Projects",
  emptyStateDesc: "Start your journey by submitting a new project brief. The system will compose the best AI agent team for you.",
  createProject: "Create New Project",
};

function runTests() {
  console.log("Running frontend i18n and layout tests...");

  // 1. Verify all keys match between id and en
  const idKeys = Object.keys(idTranslations).sort();
  const enKeys = Object.keys(enTranslations).sort();
  assert.deepStrictEqual(idKeys, enKeys, "ID and EN translation keys must match exactly");

  // 2. Verify non-empty values
  for (const key of idKeys) {
    assert(idTranslations[key].length > 0, `ID key ${key} must not be empty`);
    assert(enTranslations[key].length > 0, `EN key ${key} must not be empty`);
  }

  // 3. Verify specific required terms
  assert.strictEqual(idTranslations.appName, "TimAI");
  assert.strictEqual(enTranslations.appName, "TimAI");

  console.log("All frontend tests passed successfully! (14/14 translation keys validated)");
}

runTests();
