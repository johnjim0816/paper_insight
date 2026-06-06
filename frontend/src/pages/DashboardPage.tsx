import { CheckCircle2, Loader2 } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";

type RunState = "idle" | "running" | "done" | "error";

function statusText(state: RunState): string {
  if (state === "running") return "Running";
  if (state === "done") return "Completed";
  if (state === "error") return "Needs attention";
  return "Ready";
}

export function DashboardPage() {
  const [state, setState] = useState<RunState>("idle");
  const [message, setMessage] = useState("Local workflow is ready.");

  async function runAction(action: () => Promise<unknown>, done: string) {
    setState("running");
    setMessage("Working...");
    try {
      await action();
      setState("done");
      setMessage(done);
    } catch (error) {
      setState("error");
      setMessage(error instanceof Error ? error.message : "Request failed.");
    }
  }

  return (
    <div className="dashboard-grid">
      <section className="panel action-panel">
        <div>
          <p className="eyebrow">Daily run</p>
          <h3>Generate today's research brief</h3>
          <p className="muted">Search configured topics, summarize matched papers, and deliver the report to Feishu.</p>
        </div>
        <div className="button-row">
          <button onClick={() => runAction(api.searchPapers, "Paper search completed.")}>Search papers</button>
          <button onClick={() => runAction(api.generateReport, "Report generated.")}>Generate report</button>
          <button className="primary" onClick={() => runAction(api.generateAndSend, "Report sent to Feishu.")}>
            Send to Feishu
          </button>
        </div>
      </section>

      <section className="panel status-panel">
        <div className={`status-dot ${state}`} />
        <div>
          <p className="eyebrow">Delivery status</p>
          <h3>{statusText(state)}</h3>
          <p className="muted">{message}</p>
        </div>
        {state === "running" ? <Loader2 className="spin" size={22} /> : <CheckCircle2 size={22} />}
      </section>

      <section className="panel">
        <p className="eyebrow">Keywords</p>
        <h3>Configured in the Config page</h3>
        <p className="muted">Keep topic names short and put one keyword per line for predictable matching.</p>
      </section>

      <section className="panel">
        <p className="eyebrow">Venues</p>
        <h3>Conference and journal filters</h3>
        <p className="muted">Use names like ICLR, NeurIPS, ACL, EMNLP, Nature Machine Intelligence.</p>
      </section>
    </div>
  );
}
