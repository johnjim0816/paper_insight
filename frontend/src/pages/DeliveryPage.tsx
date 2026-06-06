import { SendHorizonal } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";

export function DeliveryPage() {
  const [status, setStatus] = useState("Not tested");

  async function sendTest() {
    setStatus("Sending test message...");
    try {
      const result = await api.sendFeishuTest();
      setStatus(`Sent: ${result.message_id ?? "ok"}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Delivery test failed");
    }
  }

  return (
    <section className="panel delivery-panel">
      <div>
        <p className="eyebrow">Delivery status</p>
        <h3>Feishu private message</h3>
        <p className="muted">{status}</p>
      </div>
      <button className="primary" onClick={() => void sendTest()}>
        <SendHorizonal size={18} />
        Send test message
      </button>
    </section>
  );
}
