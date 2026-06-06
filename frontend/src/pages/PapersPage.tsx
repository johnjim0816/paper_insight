import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Paper } from "../types";

export function PapersPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [status, setStatus] = useState("Loading papers...");

  async function load() {
    try {
      const data = await api.listPapers();
      setPapers(data);
      setStatus(data.length ? `${data.length} papers` : "No papers yet");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Load failed");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section className="panel">
      <div className="table-header">
        <div>
          <p className="eyebrow">Recent matches</p>
          <h3>{status}</h3>
        </div>
        <button className="icon-button" onClick={() => void load()} aria-label="Refresh papers">
          <RefreshCw size={18} />
        </button>
      </div>
      <div className="paper-table">
        <div className="paper-row header">
          <span>Title</span>
          <span>Venue</span>
          <span>Topics</span>
          <span>Match</span>
        </div>
        {papers.map((paper) => (
          <a className="paper-row" href={paper.url} key={paper.id}>
            <strong>{paper.title}</strong>
            <span>{paper.venue ?? paper.source}</span>
            <span>{paper.topic_names.join(", ") || "unclassified"}</span>
            <span>{paper.match_reasons.join(", ") || "matched"}</span>
          </a>
        ))}
      </div>
    </section>
  );
}
