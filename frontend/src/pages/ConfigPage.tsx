import { useEffect, useState } from "react";

import { api } from "../api/client";
import { copy, type AppCopy } from "../i18n";
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

type ConfigStatus = "loading" | "loaded" | "unsaved" | "saving" | "saved" | "error";

type ConfigPageProps = {
  t?: AppCopy;
};

function splitLines(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function withFallbackTopic(config: AppConfig): AppConfig {
  if (config.topics.length) return config;
  return Object.assign({}, config, { topics: [initialTopic] });
}

export function ConfigPage({ t = copy.zh }: ConfigPageProps) {
  const [config, setConfig] = useState<AppConfig>(initialConfig);
  const [status, setStatus] = useState<{ kind: ConfigStatus; detail?: string }>({ kind: "loading" });
  const topic = config.topics[0] ?? initialTopic;
  const statusText = status.kind === "error" ? status.detail ?? t.common.loadFailed : t.config.status[status.kind];

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const saved = await api.getConfig();
        if (active) {
          setConfig(withFallbackTopic(saved));
          setStatus({ kind: "loaded" });
        }
      } catch (error) {
        if (active) {
          setStatus({ kind: "error", detail: error instanceof Error ? error.message : undefined });
        }
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  function updateTopic(patch: Partial<TopicConfig>) {
    setConfig(Object.assign({}, config, { topics: [Object.assign({}, topic, patch)] }));
    setStatus({ kind: "unsaved" });
  }

  function updateSearch(patch: Partial<AppConfig["search"]>) {
    setConfig(Object.assign({}, config, { search: Object.assign({}, config.search, patch) }));
    setStatus({ kind: "unsaved" });
  }

  async function save() {
    setStatus({ kind: "saving" });
    try {
      const saved = await api.saveConfig(config);
      setConfig(withFallbackTopic(saved));
      setStatus({ kind: "saved" });
    } catch (error) {
      setStatus({ kind: "error", detail: error instanceof Error ? error.message : t.common.requestFailed });
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
          <p className="eyebrow">{t.config.eyebrow}</p>
          <h3>{t.config.title}</h3>
        </div>
        <span className="save-state">{statusText}</span>
      </div>

      <label>
        {t.config.labels.topicName}
        <input
          aria-label={t.config.labels.topicName}
          value={topic.name}
          onChange={(event) => updateTopic({ name: event.target.value })}
        />
      </label>

      <div className="form-grid">
        <label>
          {t.config.labels.keywords}
          <textarea
            aria-label={t.config.labels.keywords}
            value={topic.keywords.join("\n")}
            onChange={(event) => updateTopic({ keywords: splitLines(event.target.value) })}
          />
        </label>
        <label>
          {t.config.labels.venues}
          <textarea
            aria-label={t.config.labels.venues}
            value={topic.venues.join("\n")}
            onChange={(event) => updateTopic({ venues: splitLines(event.target.value) })}
          />
        </label>
        <label>
          {t.config.labels.excludeKeywords}
          <textarea
            aria-label={t.config.labels.excludeKeywords}
            value={topic.exclude_keywords.join("\n")}
            onChange={(event) => updateTopic({ exclude_keywords: splitLines(event.target.value) })}
          />
        </label>
      </div>

      <div className="numeric-row">
        <label>
          {t.config.labels.lookbackDays}
          <input
            type="number"
            min={1}
            max={60}
            value={config.search.lookback_days}
            onChange={(event) => updateSearch({ lookback_days: Number(event.target.value) })}
          />
        </label>
        <label>
          {t.config.labels.maxResults}
          <input
            type="number"
            min={1}
            max={100}
            value={config.search.max_results_per_source}
            onChange={(event) => updateSearch({ max_results_per_source: Number(event.target.value) })}
          />
        </label>
      </div>

      <button className="primary" type="submit">
        {t.config.save}
      </button>
    </form>
  );
}
