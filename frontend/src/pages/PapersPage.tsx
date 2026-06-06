import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy, type AppCopy } from "../i18n";
import type { Paper } from "../types";

type PapersStatus = { kind: "loading" } | { kind: "count"; count: number } | { kind: "empty" } | { kind: "error"; detail: string };

type PapersPageProps = {
  t?: AppCopy;
};

function statusText(t: AppCopy, status: PapersStatus): string {
  if (status.kind === "count") return t.papers.count(status.count);
  if (status.kind === "empty") return t.papers.empty;
  if (status.kind === "error") return status.detail;
  return t.papers.loading;
}

export function PapersPage({ t = copy.zh }: PapersPageProps) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [status, setStatus] = useState<PapersStatus>({ kind: "loading" });

  async function load() {
    try {
      const data = await api.listPapers();
      setPapers(data);
      setStatus(data.length ? { kind: "count", count: data.length } : { kind: "empty" });
    } catch (error) {
      setStatus({ kind: "error", detail: error instanceof Error ? error.message : t.common.loadFailed });
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <div className="table-header">
        <div>
          <p className="eyebrow">{t.papers.eyebrow}</p>
          <h3>{statusText(t, status)}</h3>
        </div>
        <button className="icon-button" onClick={() => void load()} aria-label={t.papers.refresh}>
          <RefreshCw size={18} />
        </button>
      </div>
      <div className="paper-table">
        <div className="paper-row header">
          <span>{t.papers.columns.title}</span>
          <span>{t.papers.columns.venue}</span>
          <span>{t.papers.columns.topics}</span>
          <span>{t.papers.columns.match}</span>
        </div>
        {papers.map((paper) => (
          <a className="paper-row" href={paper.url} key={paper.id}>
            <strong>{paper.title}</strong>
            <span>{paper.venue ?? paper.source}</span>
            <span>{paper.topic_names.join(", ") || t.common.unclassified}</span>
            <span>{paper.match_reasons.join(", ") || t.common.matched}</span>
          </a>
        ))}
      </div>
    </section>
  );
}
