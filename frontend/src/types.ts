export type TopicConfig = {
  name: string;
  keywords: string[];
  venues: string[];
  exclude_keywords: string[];
};

export type AppConfig = {
  topics: TopicConfig[];
  search: { lookback_days: number; max_results_per_source: number };
  summary: { language: string };
  delivery: { provider: string; mode: string; recipient_id_type: string };
};

export type Paper = {
  id: number;
  dedup_key: string;
  source: string;
  title: string;
  abstract: string | null;
  authors: string[];
  venue: string | null;
  published_at: string | null;
  url: string;
  doi: string | null;
  arxiv_id: string | null;
  semantic_scholar_id: string | null;
  citation_count: number | null;
  match_reasons: string[];
  topic_names: string[];
};

export type Report = {
  id: number;
  report_date: string;
  title: string;
  markdown: string;
};

export type DeliveryResult = {
  status: string;
  message_id?: string;
  detail?: string;
};
