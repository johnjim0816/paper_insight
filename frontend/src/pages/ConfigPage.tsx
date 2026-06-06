import { useState } from "react";

import { api } from "../api/client";
import type { AppConfig, TopicConfig } from "../types";

const initialTopic: TopicConfig = {
  name: "llm_agents",
  keywords: ["LLM agent", "tool use", "autonomous agents"],
  venues: ["ICLR", "NeurIPS", "ACL"],
  exclude_keywords: ["survey"]
};

const initialConfig: AppConfig = {
  topics: [initialTopic],
  search: { lookback_days: 7, max_results_per_source: 30 },
  summary: { language: "zh" },
  delivery: { provider: "feishu", mode: "app_bot", recipient_id_type: "email" }
};

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ConfigPage() {
  const [config, setConfig] = useState<AppConfig>(initialConfig);
  const [status, setStatus] = useState("Unsaved local edits");
  const topic = config.topics[0] ?? initialTopic;

  function updateTopic(patch: Partial<TopicConfig>) {
    setConfig(Object.assign({}, config, { topics: [Object.assign({}, topic, patch)] }));
  }

  async function save() {
    setStatus("Saving...");
    try {
      const saved = await api.saveConfig(config);
      setConfig(saved);
      setStatus("Saved");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Save failed");
    }
  }

  return (
    <form
      className="panel config-form"
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <div className="form-header">
        <div>
          <p className="eyebrow">Config</p>
          <h3>Topic and source matching</h3>
        </div>
        <span className="save-state">{status}</span>
      </div>

      <label>
        Topic name
        <input aria-label="Topic name" value={topic.name} onChange={(event) => updateTopic({ name: event.target.value })} />
      </label>

      <div className="form-grid">
        <label>
          Keywords
          <textarea
            aria-label="Keywords"
            value={topic.keywords.join("\n")}
            onChange={(event) => updateTopic({ keywords: splitLines(event.target.value) })}
          />
        </label>
        <label>
          Venues
          <textarea
            aria-label="Venues"
            value={topic.venues.join("\n")}
            onChange={(event) => updateTopic({ venues: splitLines(event.target.value) })}
          />
        </label>
        <label>
          Exclude keywords
          <textarea
            aria-label="Exclude keywords"
            value={topic.exclude_keywords.join("\n")}
            onChange={(event) => updateTopic({ exclude_keywords: splitLines(event.target.value) })}
          />
        </label>
      </div>

      <div className="numeric-row">
        <label>
          Lookback days
          <input
            type="number"
            min={1}
            max={60}
            value={config.search.lookback_days}
            onChange={(event) =>
              setConfig(
                Object.assign({}, config, {
                  search: Object.assign({}, config.search, { lookback_days: Number(event.target.value) })
                })
              )
            }
          />
        </label>
        <label>
          Max results per source
          <input
            type="number"
            min={1}
            max={100}
            value={config.search.max_results_per_source}
            onChange={(event) =>
              setConfig(
                Object.assign({}, config, {
                  search: Object.assign({}, config.search, { max_results_per_source: Number(event.target.value) })
                })
              )
            }
          />
        </label>
      </div>

      <button className="primary" type="submit">
        Save config
      </button>
    </form>
  );
}
