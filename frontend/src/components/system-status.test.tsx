import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SystemStatus } from "./system-status";

describe("SystemStatus", () => {
  it("reports degraded services in text, not only colour", () => {
    render(
      <SystemStatus
        state={{ status: "success", data: { status: "degraded", checks: { database: "ok", redis: "error" } } }}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(screen.getByText("Database").nextSibling).toHaveTextContent("Connected");
    expect(screen.getByText("Redis (job queue)").nextSibling).toHaveTextContent("Unavailable");
  });
});
