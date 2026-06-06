import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ConfigPage } from "./ConfigPage";

test("renders config controls", () => {
  render(<ConfigPage />);
  expect(screen.getByLabelText("Topic name")).toBeInTheDocument();
  expect(screen.getByLabelText("Keywords")).toBeInTheDocument();
  expect(screen.getByLabelText("Venues")).toBeInTheDocument();
  expect(screen.getByLabelText("Exclude keywords")).toBeInTheDocument();
});
