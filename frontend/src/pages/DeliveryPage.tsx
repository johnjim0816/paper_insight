import { SendHorizonal } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";
import { copy, type AppCopy } from "../i18n";

type DeliveryStatus =
  | { kind: "notTested" }
  | { kind: "sending" }
  | { kind: "sent"; messageId: string }
  | { kind: "error"; detail: string };

type DeliveryPageProps = {
  t?: AppCopy;
};

function statusText(t: AppCopy, status: DeliveryStatus): string {
  if (status.kind === "sending") return t.delivery.sending;
  if (status.kind === "sent") return t.delivery.sent(status.messageId);
  if (status.kind === "error") return status.detail;
  return t.delivery.notTested;
}

export function DeliveryPage({ t = copy.zh }: DeliveryPageProps) {
  const [status, setStatus] = useState<DeliveryStatus>({ kind: "notTested" });

  async function sendTest() {
    setStatus({ kind: "sending" });
    try {
      const result = await api.sendFeishuTest();
      setStatus({ kind: "sent", messageId: result.message_id ?? t.common.ok });
    } catch (error) {
      setStatus({ kind: "error", detail: error instanceof Error ? error.message : t.delivery.failed });
    }
  }

  return (
    <section className="panel delivery-panel">
      <div>
        <p className="eyebrow">{t.delivery.eyebrow}</p>
        <h3>{t.delivery.title}</h3>
        <p className="muted">{statusText(t, status)}</p>
      </div>
      <button className="primary" onClick={() => void sendTest()}>
        <SendHorizonal size={18} />
        {t.delivery.sendTest}
      </button>
    </section>
  );
}
