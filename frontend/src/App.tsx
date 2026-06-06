import { BookOpen, FileText, Home, Languages, Send, Settings } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";

import { copy, type AppCopy, type Language } from "./i18n";
import { ConfigPage } from "./pages/ConfigPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DeliveryPage } from "./pages/DeliveryPage";
import { PapersPage } from "./pages/PapersPage";
import { ReportsPage } from "./pages/ReportsPage";
import "./styles.css";

type Page = "dashboard" | "config" | "papers" | "reports" | "delivery";

const nav: { key: Page; icon: LucideIcon }[] = [
  { key: "dashboard", icon: Home },
  { key: "config", icon: Settings },
  { key: "papers", icon: BookOpen },
  { key: "reports", icon: FileText },
  { key: "delivery", icon: Send }
];

function renderPage(page: Page, t: AppCopy) {
  if (page === "config") return <ConfigPage t={t} />;
  if (page === "papers") return <PapersPage t={t} />;
  if (page === "reports") return <ReportsPage t={t} />;
  if (page === "delivery") return <DeliveryPage t={t} />;
  return <DashboardPage t={t} />;
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [language, setLanguage] = useState<Language>("zh");
  const t = copy[language];
  const currentLabel = t.nav[page];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">PI</div>
          <h1>Paper Insight</h1>
        </div>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={page === item.key ? "active" : ""} onClick={() => setPage(item.key)}>
                <Icon size={18} />
                <span>{t.nav[item.key]}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{t.shell.eyebrow}</p>
            <h2>{currentLabel}</h2>
          </div>
          <div className="topbar-actions">
            <div className="language-switch" aria-label={t.language.label}>
              <Languages size={16} />
              <button
                className={language === "zh" ? "active" : ""}
                onClick={() => setLanguage("zh")}
                type="button"
                aria-pressed={language === "zh"}
              >
                {t.language.zh}
              </button>
              <button
                className={language === "en" ? "active" : ""}
                onClick={() => setLanguage("en")}
                type="button"
                aria-pressed={language === "en"}
              >
                {t.language.en}
              </button>
            </div>
            <div className="topbar-status">{t.shell.apiStatus}</div>
          </div>
        </header>
        {renderPage(page, t)}
      </main>
    </div>
  );
}
