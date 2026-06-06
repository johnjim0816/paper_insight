import { CheckCircle2, Loader2 } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";
import { copy, type AppCopy } from "../i18n";

type RunState = "idle" | "running" | "done" | "error";
type DashboardMessage =
  | { kind: "ready" }
  | { kind: "working" }
  | { kind: "searchDone"; count: number; warnings: string[] }
  | { kind: "searchEmpty"; warnings: string[] }
  | { kind: "reportGenerated" }
  | { kind: "reportSent" }
  | { kind: "error"; detail: string };

type DashboardPageProps = {
  t?: AppCopy;
};

function statusText(t: AppCopy, state: RunState): string {
  return t.dashboard.states[state];
}

function messageText(t: AppCopy, message: DashboardMessage): string {
  if (message.kind === "working") return t.dashboard.messages.working;
  if (message.kind === "reportGenerated") return t.dashboard.messages.reportGenerated;
  if (message.kind === "reportSent") return t.dashboard.messages.reportSent;
  if (message.kind === "error") return message.detail;
  if (message.kind === "searchDone") {
    const warning = message.warnings.length ? ` ${t.dashboard.messages.warning(message.warnings)}` : "";
    return `${t.dashboard.messages.searchDone(message.count)}${warning}`;
  }
  if (message.kind === "searchEmpty") {
    const warning = message.warnings.length ? ` ${t.dashboard.messages.warning(message.warnings)}` : "";
    return `${t.dashboard.messages.searchEmpty}${warning}`;
  }
  return t.dashboard.messages.ready;
}

export function DashboardPage({ t = copy.zh }: DashboardPageProps) {
  const [state, setState] = useState<RunState>("idle");
  const [message, setMessage] = useState<DashboardMessage>({ kind: "ready" });

  async function runAction<T>(action: () => Promise<T>, done: (result: T) => DashboardMessage) {
    setState("running");
    setMessage({ kind: "working" });
    try {
      const result = await action();
      setState("done");
      setMessage(done(result));
    } catch (error) {
      setState("error");
      setMessage({ kind: "error", detail: error instanceof Error ? error.message : t.common.requestFailed });
    }
  }

  return (
    <div className="dashboard-grid">
      <section className="panel action-panel">
        <div>
          <p className="eyebrow">{t.dashboard.dailyRun}</p>
          <h3>{t.dashboard.title}</h3>
          <p className="muted">{t.dashboard.description}</p>
        </div>
        <div className="button-row">
          <button
            onClick={() =>
              runAction(api.searchPapers, (result) =>
                result.count
                  ? { kind: "searchDone", count: result.count, warnings: result.warnings }
                  : { kind: "searchEmpty", warnings: result.warnings }
              )
            }
          >
            {t.dashboard.searchPapers}
          </button>
          <button onClick={() => runAction(api.generateReport, () => ({ kind: "reportGenerated" }))}>
            {t.dashboard.generateReport}
          </button>
          <button className="primary" onClick={() => runAction(api.generateAndSend, () => ({ kind: "reportSent" }))}>
            {t.dashboard.sendToFeishu}
          </button>
        </div>
      </section>

      <section className="panel status-panel">
        <div className={`status-dot ${state}`} />
        <div>
          <p className="eyebrow">{t.dashboard.statusEyebrow}</p>
          <h3>{statusText(t, state)}</h3>
          <p className="muted">{messageText(t, message)}</p>
        </div>
        {state === "running" ? <Loader2 className="spin" size={22} /> : <CheckCircle2 size={22} />}
      </section>

      <section className="panel">
        <p className="eyebrow">{t.dashboard.keywordsEyebrow}</p>
        <h3>{t.dashboard.keywordsTitle}</h3>
        <p className="muted">{t.dashboard.keywordsDescription}</p>
      </section>

      <section className="panel">
        <p className="eyebrow">{t.dashboard.venuesEyebrow}</p>
        <h3>{t.dashboard.venuesTitle}</h3>
        <p className="muted">{t.dashboard.venuesDescription}</p>
      </section>
    </div>
  );
}
