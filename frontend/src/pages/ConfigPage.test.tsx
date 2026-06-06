import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

test("renders and saves multiple research topics", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
    if (init?.method === "PUT") {
      return new Response(init.body as BodyInit, {
        headers: { "Content-Type": "application/json" },
        status: 200
      });
    }
    return new Response(
      JSON.stringify({
        topics: [
          {
            name: "RL",
            keywords: ["reinforcement learning"],
            venues: ["NeurIPS"],
            exclude_keywords: []
          },
          {
            name: "worldmodel",
            keywords: ["world model"],
            venues: ["ICLR"],
            exclude_keywords: []
          }
        ],
        search: { lookback_days: 7, max_results_per_source: 30 },
        summary: { language: "zh" },
        delivery: { provider: "feishu", mode: "app_bot", recipient_id_type: "email" }
      }),
      { headers: { "Content-Type": "application/json" }, status: 200 }
    );
  });

  render(<ConfigPage />);

  await waitFor(() => {
    expect(screen.getByDisplayValue("RL")).toBeInTheDocument();
    expect(screen.getByDisplayValue("worldmodel")).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: "新增主题" }));
  fireEvent.change(screen.getAllByLabelText("主题名称")[2], { target: { value: "robotics" } });
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

  await waitFor(() => {
    const saveCall = fetchMock.mock.calls.find((call) => call[1]?.method === "PUT");
    expect(saveCall).toBeDefined();
    expect(JSON.parse(saveCall?.[1]?.body as string).topics.map((topic: { name: string }) => topic.name)).toEqual([
      "RL",
      "worldmodel",
      "robotics"
    ]);
  });
});
