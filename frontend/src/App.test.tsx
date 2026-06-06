import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

test("defaults to Chinese and switches to English", () => {
  render(<App />);
  expect(screen.getByText("Paper Insight")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "仪表盘" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "查找论文" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "生成报告" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "发送到飞书" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "English" }));

  expect(screen.getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Search papers" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Generate report" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Send to Feishu" })).toBeInTheDocument();
});

test("shows the number of papers found after search", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ count: 2, papers: [], warnings: [] }), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );

  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: "查找论文" }));

  await waitFor(() => {
    expect(screen.getByText("找到 2 篇论文，可到论文页查看。")).toBeInTheDocument();
  });
});
