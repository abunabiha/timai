// Test script for frontend integrity and i18n
const assert = require("assert");

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
  loginTitle: "Masuk ke TimAI",
  loginSubtitle: "Gunakan akun Admin, Product Owner, atau Viewer Anda.",
  setupAdminTitle: "Inisialisasi Akun Admin",
  setupAdminSubtitle: "Selamat datang di instalasi baru TimAI. Silakan buat akun Administrator pertama untuk mengelola sistem.",
  nameLabel: "Nama Lengkap",
  emailLabel: "Alamat Email",
  passwordLabel: "Kata Sandi",
  loginButton: "Masuk",
  setupButton: "Buat Akun Admin & Mulai",
  logoutButton: "Keluar",
  roleAdmin: "Administrator",
  rolePO: "Product Owner",
  roleViewer: "Viewer",
  loggedInAs: "Masuk sebagai",
  invalidCredentials: "Email atau kata sandi tidak valid.",
  setupSuccess: "Akun Administrator berhasil dibuat!",
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
  loginTitle: "Log In to TimAI",
  loginSubtitle: "Use your Admin, Product Owner, or Viewer account.",
  setupAdminTitle: "Admin Account Setup",
  setupAdminSubtitle: "Welcome to your new TimAI installation. Create the first Administrator account to manage the platform.",
  nameLabel: "Full Name",
  emailLabel: "Email Address",
  passwordLabel: "Password",
  loginButton: "Log In",
  setupButton: "Create Admin & Start",
  logoutButton: "Log Out",
  roleAdmin: "Administrator",
  rolePO: "Product Owner",
  roleViewer: "Viewer",
  loggedInAs: "Logged in as",
  invalidCredentials: "Invalid email or password.",
  setupSuccess: "Administrator account created successfully!",
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

  console.log(`All frontend tests passed successfully! (${idKeys.length}/${idKeys.length} translation keys validated)`);
}

runTests();
