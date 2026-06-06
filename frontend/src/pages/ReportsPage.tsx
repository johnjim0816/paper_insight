import { Send } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy, type AppCopy } from "../i18n";
import type { Report } from "../types";

type ReportsStatus =
  | { kind: "loading" }
  | { kind: "count"; count: number }
  | { kind: "empty" }
  | { kind: "sending" }
  | { kind: "sent" }
  | { kind: "error"; detail: string };

type ReportsPageProps = {
  t?: AppCopy;
};

function statusText(t: AppCopy, status: ReportsStatus): string {
  if (status.kind === "count") return t.reports.count(status.count);
  if (status.kind === "empty") return t.reports.empty;
  if (status.kind === "sending") return t.reports.sending;
  if (status.kind === "sent") return t.reports.sent;
  if (status.kind === "error") return status.detail;
  return t.reports.loading;
}

export function ReportsPage({ t = copy.zh }: ReportsPageProps) {
  const [reports, setReports] = useState<Report[]>([]);
  const [status, setStatus] = useState<ReportsStatus>({ kind: "loading" });

  async function load() {
    try {
      const data = await api.listReports();
      setReports(data);
      setStatus(data.length ? { kind: "count", count: data.length } : { kind: "empty" });
    } catch (error) {
      setStatus({ kind: "error", detail: error instanceof Error ? error.message : t.common.loadFailed });
    }
  }

  async function send(reportId: number) {
    setStatus({ kind: "sending" });
    try {
      await api.sendReport(reportId);
      setStatus({ kind: "sent" });
    } catch (error) {
      setStatus({ kind: "error", detail: error instanceof Error ? error.message : t.common.requestFailed });
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="stack">
      <section className="panel table-header">
        <div>
          <p className="eyebrow">{t.reports.eyebrow}</p>
          <h3>{statusText(t, status)}</h3>
        </div>
      </section>
      {reports.map((report) => (
        <article className="panel report-preview" key={report.id}>
          <div className="report-title">
            <div>
              <p className="eyebrow">{report.report_date}</p>
              <h3>{report.title}</h3>
            </div>
            <button className="icon-button" onClick={() => void send(report.id)} aria-label={t.reports.sendReport(report.title)}>
              <Send size={18} />
            </button>
          </div>
          <pre>{report.markdown}</pre>
        </article>
      ))}
    </div>
  );
}
