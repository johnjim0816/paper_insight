import { Plus, Trash2 } from "lucide-react";
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

function blankTopic(index: number): TopicConfig {
  return {
    name: `topic_${index}`,
    keywords: [],
    venues: [],
    exclude_keywords: []
  };
}

export function ConfigPage({ t = copy.zh }: ConfigPageProps) {
  const [config, setConfig] = useState<AppConfig>(initialConfig);
  const [status, setStatus] = useState<{ kind: ConfigStatus; detail?: string }>({ kind: "loading" });
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

  function updateTopic(index: number, patch: Partial<TopicConfig>) {
    setConfig((current) =>
      Object.assign({}, current, {
        topics: current.topics.map((topic, topicIndex) =>
          topicIndex === index ? Object.assign({}, topic, patch) : topic
        )
      })
    );
    setStatus({ kind: "unsaved" });
  }

  function addTopic() {
    setConfig((current) => Object.assign({}, current, { topics: [...current.topics, blankTopic(current.topics.length + 1)] }));
    setStatus({ kind: "unsaved" });
  }

  function removeTopic(index: number) {
    setConfig((current) => {
      if (current.topics.length <= 1) return current;
      return Object.assign({}, current, { topics: current.topics.filter((_, topicIndex) => topicIndex !== index) });
    });
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

      <div className="topic-list">
        {config.topics.map((topic, index) => (
          <section className="topic-block" key={`${index}-${topic.name}`}>
            <div className="topic-block-header">
              <div>
                <p className="eyebrow">{t.config.topicHeading(index + 1)}</p>
                <h4>{topic.name || t.config.untitledTopic}</h4>
              </div>
              {config.topics.length > 1 ? (
                <button
                  aria-label={t.config.removeTopic(topic.name || t.config.untitledTopic)}
                  className="icon-button subtle-danger"
                  onClick={() => removeTopic(index)}
                  type="button"
                >
                  <Trash2 size={17} />
                </button>
              ) : null}
            </div>

            <label>
              {t.config.labels.topicName}
              <input
                aria-label={t.config.labels.topicName}
                value={topic.name}
                onChange={(event) => updateTopic(index, { name: event.target.value })}
              />
            </label>

            <div className="form-grid">
              <label>
                {t.config.labels.keywords}
                <textarea
                  aria-label={t.config.labels.keywords}
                  value={topic.keywords.join("\n")}
                  onChange={(event) => updateTopic(index, { keywords: splitLines(event.target.value) })}
                />
              </label>
              <label>
                {t.config.labels.venues}
                <textarea
                  aria-label={t.config.labels.venues}
                  value={topic.venues.join("\n")}
                  onChange={(event) => updateTopic(index, { venues: splitLines(event.target.value) })}
                />
              </label>
              <label>
                {t.config.labels.excludeKeywords}
                <textarea
                  aria-label={t.config.labels.excludeKeywords}
                  value={topic.exclude_keywords.join("\n")}
                  onChange={(event) => updateTopic(index, { exclude_keywords: splitLines(event.target.value) })}
                />
              </label>
            </div>
          </section>
        ))}
      </div>

      <button className="secondary-action" type="button" onClick={addTopic}>
        <Plus size={17} />
        {t.config.addTopic}
      </button>

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
