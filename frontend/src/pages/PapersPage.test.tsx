import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { PapersPage } from "./PapersPage";

afterEach(() => {
  vi.restoreAllMocks();
});

test("searches papers for the selected topic", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/api/config")) {
      return new Response(
        JSON.stringify({
          topics: [
            { name: "RL", keywords: ["reinforcement learning"], venues: ["NeurIPS"], exclude_keywords: [] },
            { name: "worldmodel", keywords: ["world model"], venues: ["ICLR"], exclude_keywords: [] }
          ],
          search: { lookback_days: 7, max_results_per_source: 30 },
          summary: { language: "zh" },
          delivery: { provider: "feishu", mode: "app_bot", recipient_id_type: "email" }
        }),
        { headers: { "Content-Type": "application/json" }, status: 200 }
      );
    }
    if (url.includes("/api/papers/search")) {
      return new Response(
        JSON.stringify({
          count: 1,
          warnings: [],
          papers: [
            {
              id: 1,
              dedup_key: "doi:10.1000/rl",
              source: "fake",
              title: "Deep Reinforcement Learning",
              abstract: null,
              authors: ["Alice"],
              venue: "NeurIPS",
              published_at: "2026-06-05",
              url: "https://example.com/rl",
              doi: "10.1000/rl",
              arxiv_id: null,
              semantic_scholar_id: null,
              citation_count: 8,
              topic_names: ["RL"],
              match_reasons: ["keyword: reinforcement learning"]
            }
          ]
        }),
        { headers: { "Content-Type": "application/json" }, status: 200 }
      );
    }
    return new Response(JSON.stringify([]), { headers: { "Content-Type": "application/json" }, status: 200 });
  });

  render(<PapersPage />);

  await waitFor(() => {
    expect(screen.getByRole("option", { name: "RL" })).toBeInTheDocument();
  });

  fireEvent.change(screen.getByLabelText("搜索主题"), { target: { value: "RL" } });
  fireEvent.click(screen.getByRole("button", { name: "搜索选中主题" }));

  await waitFor(() => {
    expect(screen.getByText("Deep Reinforcement Learning")).toBeInTheDocument();
  });
  expect(fetchMock).toHaveBeenCalledWith(
    "http://127.0.0.1:8000/api/papers/search?topic=RL",
    expect.objectContaining({ method: "POST" })
  );
});
