import { Send } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Report } from "../types";

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [status, setStatus] = useState("Loading reports...");

  async function load() {
    try {
      const data = await api.listReports();
      setReports(data);
      setStatus(data.length ? `${data.length} reports` : "No reports yet");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Load failed");
    }
  }

  async function send(reportId: number) {
    setStatus("Sending...");
    try {
      await api.sendReport(reportId);
      setStatus("Report sent");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Send failed");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="stack">
      <section className="panel table-header">
        <div>
          <p className="eyebrow">Latest report</p>
          <h3>{status}</h3>
        </div>
      </section>
      {reports.map((report) => (
        <article className="panel report-preview" key={report.id}>
          <div className="report-title">
            <div>
              <p className="eyebrow">{report.report_date}</p>
              <h3>{report.title}</h3>
            </div>
            <button className="icon-button" onClick={() => void send(report.id)} aria-label={`Send ${report.title}`}>
              <Send size={18} />
            </button>
          </div>
          <pre>{report.markdown}</pre>
        </article>
      ))}
    </div>
  );
}
