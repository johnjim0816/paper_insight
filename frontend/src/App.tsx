import { BookOpen, FileText, Home, Send, Settings } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";

import { ConfigPage } from "./pages/ConfigPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DeliveryPage } from "./pages/DeliveryPage";
import { PapersPage } from "./pages/PapersPage";
import { ReportsPage } from "./pages/ReportsPage";
import "./styles.css";

type Page = "dashboard" | "config" | "papers" | "reports" | "delivery";

const nav: { key: Page; label: string; icon: LucideIcon }[] = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "config", label: "Config", icon: Settings },
  { key: "papers", label: "Papers", icon: BookOpen },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "delivery", label: "Feishu", icon: Send }
];

function renderPage(page: Page) {
  if (page === "config") return <ConfigPage />;
  if (page === "papers") return <PapersPage />;
  if (page === "reports") return <ReportsPage />;
  if (page === "delivery") return <DeliveryPage />;
  return <DashboardPage />;
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const currentLabel = nav.find((item) => item.key === page)?.label ?? "Dashboard";

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
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Local research monitor</p>
            <h2>{currentLabel}</h2>
          </div>
          <div className="topbar-status">FastAPI: 127.0.0.1:8000</div>
        </header>
        {renderPage(page)}
      </main>
    </div>
  );
}
