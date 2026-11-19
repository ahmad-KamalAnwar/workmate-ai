import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError, type Task } from "@/lib/api/client";

import { TaskList } from "./task-list";

const task: Task = {
  id: "7d1f0c3e-0000-4000-8000-000000000001",
  title: "Summarise unread Slack messages",
  source: "chat",
  status: "awaiting_approval",
  error: null,
  created_at: "2026-11-19T08:00:00Z",
  started_at: null,
  finished_at: null,
};

describe("TaskList", () => {
  it("shows a loading state", () => {
    render(<TaskList state={{ status: "loading" }} onRetry={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading tasks");
  });

  it("shows an empty state", () => {
    render(<TaskList state={{ status: "success", data: [] }} onRetry={vi.fn()} />);
    expect(screen.getByText(/No tasks yet/)).toBeInTheDocument();
  });

  it("lists tasks with readable status", () => {
    render(<TaskList state={{ status: "success", data: [task] }} onRetry={vi.fn()} />);
    expect(screen.getByRole("listitem")).toHaveTextContent("Summarise unread Slack messages");
    expect(screen.getByText("awaiting approval")).toBeInTheDocument();
  });

  it("shows errors with a working retry", async () => {
    const onRetry = vi.fn();
    const error = new ApiError(0, "network_error", "Could not reach the server.");
    render(<TaskList state={{ status: "error", error }} onRetry={onRetry} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Could not reach the server.");
    await userEvent.setup().click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
