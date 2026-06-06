import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ConfigPage } from "./ConfigPage";

afterEach(() => {
  vi.restoreAllMocks();
});

test("renders Chinese config controls and loads backend config", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        topics: [
          {
            name: "llm_agents",
            keywords: ["LLM agent", "tool use"],
            venues: ["ICLR", "NeurIPS"],
            exclude_keywords: ["survey"]
          }
        ],
        search: { lookback_days: 7, max_results_per_source: 30 },
        summary: { language: "zh" },
        delivery: { provider: "feishu", mode: "app_bot", recipient_id_type: "email" }
      }),
      { headers: { "Content-Type": "application/json" }, status: 200 }
    )
  );

  render(<ConfigPage />);

  expect(screen.getByLabelText("主题名称")).toBeInTheDocument();
  expect(screen.getByLabelText("关键词")).toBeInTheDocument();
  expect(screen.getByLabelText("会议/期刊")).toBeInTheDocument();
  expect(screen.getByLabelText("排除关键词")).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByDisplayValue("llm_agents")).toBeInTheDocument();
  });
});
