import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import App from "./App";

test("renders app shell and primary workflow actions", () => {
  render(<App />);
  expect(screen.getByText("Paper Insight")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Search papers/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Generate report/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Send to Feishu/i })).toBeInTheDocument();
});
